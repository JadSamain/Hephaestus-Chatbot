# server_mcp_movies_and_showtimes.py
# ------------------------------------------------------------
# MCP server unique qui expose 3 tools :
#   1) search_movie(title, limit=10, include_details=False)
#   2) get_movie(movie_id)
#   3) cinefil_showtimes(film_seances_url, city=None, major_cities=True, limit_cinemas_per_city=10)
#
# Movies:
#   - Source principale: CSV (KB)
#   - Fallback: scraping MovieOfTheNight (SPA) via Playwright
#   - Refresh: rating (TTL court) + détails (TTL long) + remplissage si manquant
#
# Showtimes:
#   - Source: cinefil.com (/film/<slug>/seances[/<ville>])
#   - Scraping HTML via httpx + BeautifulSoup
#   - Cache disque (TTL 2h) par URL
#   - Sortie groupée par cinéma avec noms (cinemas[].cinema)
#
# Install:
#   pip install mcp pandas playwright httpx beautifulsoup4
#   playwright install
#
# Run:
#   export MOVIES_CSV_PATH="data/movies_catalog_fr.csv"
#   python server_mcp_movies_and_showtimes.py
# ------------------------------------------------------------

from __future__ import annotations

import os
import re
import json
import time
import hashlib
import unicodedata
import asyncio
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urlparse, parse_qs

import pandas as pd
import httpx
from bs4 import BeautifulSoup, Tag
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

from mcp.server.fastmcp import FastMCP


# ============================================================
# MCP Server (ONE instance)
# ============================================================
mcp = FastMCP("hephaestus-movies-and-showtimes")


# ============================================================
# PART A — MOVIES: CSV KB + MovieOfTheNight fallback
# ============================================================
MOVIES_CSV_PATH = os.getenv("MOVIES_CSV_PATH", "data/movies_catalog_fr.csv")
MOTN_BASE_URL = "https://www.movieofthenight.com"

MOVIES_RATING_TTL_SECONDS = int(os.getenv("RATING_TTL_SECONDS", str(24 * 3600)))          # 24h
MOVIES_DETAILS_TTL_SECONDS = int(os.getenv("DETAILS_TTL_SECONDS", str(30 * 24 * 3600)))  # 30j
MOVIES_WRITE_LOCK_PATH = os.getenv("CSV_LOCK_PATH", MOVIES_CSV_PATH + ".lock")


def _now_ts() -> int:
    return int(time.time())


def _normalize_text(s: Any) -> str:
    s = "" if s is None else str(s)
    s = s.strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def _safe_int(x: Any) -> Optional[int]:
    try:
        if pd.isna(x):
            return None
        return int(float(x))
    except Exception:
        return None


def _safe_float(x: Any) -> Optional[float]:
    try:
        if pd.isna(x):
            return None
        return float(x)
    except Exception:
        return None


def _safe_str(x: Any) -> Optional[str]:
    if x is None:
        return None
    try:
        if pd.isna(x):
            return None
    except Exception:
        pass
    s = str(x).strip()
    return s if s else None


def _pick_col(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    for c in candidates:
        if c in df.columns:
            return c
    return None


def _parse_ts(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        if isinstance(value, float) and pd.isna(value):
            return None
    except Exception:
        pass
    try:
        return int(float(value))
    except Exception:
        pass
    try:
        return int(datetime.fromisoformat(str(value)).timestamp())
    except Exception:
        return None


def _ensure_movie_columns(df: pd.DataFrame) -> pd.DataFrame:
    required = {
        "motn_url": None,
        "summary": None,
        "starring": None,
        "director": None,
        "year": None,
        "rating": None,
        "rating_last_updated_at": None,
        "details_last_updated_at": None,
    }
    for col, default in required.items():
        if col not in df.columns:
            df[col] = default
    return df


def _acquire_file_lock(lock_path: str, timeout: int = 10) -> None:
    start = time.time()
    while True:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            return
        except FileExistsError:
            if time.time() - start > timeout:
                raise TimeoutError("Could not acquire CSV lock (timeout).")
            time.sleep(0.05)


def _release_file_lock(lock_path: str) -> None:
    try:
        os.remove(lock_path)
    except FileNotFoundError:
        pass


def _atomic_write_csv(df: pd.DataFrame, path: str) -> None:
    tmp = path + ".tmp"
    df.to_csv(tmp, index=False)
    os.replace(tmp, path)


# ---- Load movies KB (CSV)
if not os.path.exists(MOVIES_CSV_PATH):
    raise FileNotFoundError(f"Movies CSV not found: {MOVIES_CSV_PATH}")

MOVIES_DF = pd.read_csv(MOVIES_CSV_PATH)
MOVIES_DF = _ensure_movie_columns(MOVIES_DF)

MOV_COL_ID = _pick_col(MOVIES_DF, ["show_id", "id", "movie_id", "ID", "internal_id"])
MOV_COL_TITLE = _pick_col(MOVIES_DF, ["title", "Titre", "name", "Name"])
MOV_COL_YEAR_LEGACY = _pick_col(MOVIES_DF, ["year", "Year", "annee", "Année"])

if MOV_COL_TITLE is None:
    raise ValueError("No title column found in movies CSV (expected title/Titre/name/Name).")

if "_title_norm" not in MOVIES_DF.columns:
    MOVIES_DF["_title_norm"] = MOVIES_DF[MOV_COL_TITLE].astype(str).map(_normalize_text)


def _persist_movies_df() -> None:
    global MOVIES_DF
    _acquire_file_lock(MOVIES_WRITE_LOCK_PATH)
    try:
        _atomic_write_csv(MOVIES_DF, MOVIES_CSV_PATH)
    finally:
        _release_file_lock(MOVIES_WRITE_LOCK_PATH)


# ---- MovieOfTheNight scraping helpers
def _extract_id_from_motn_url(motn_url: str) -> Optional[str]:
    try:
        u = urlparse(motn_url)
        qs = parse_qs(u.query)
        if "id" in qs and qs["id"]:
            return str(qs["id"][0])
        m = re.search(r"/show/(\d+)", u.path)
        if m:
            return m.group(1)
    except Exception:
        pass
    return None


def _first_str(x: Any) -> Optional[str]:
    if isinstance(x, str):
        s = x.strip()
        return s if s else None
    return None


def _coerce_year(x: Any) -> Optional[int]:
    if x is None:
        return None
    if isinstance(x, int):
        return x if 1900 <= x <= 2100 else None
    if isinstance(x, str):
        m = re.search(r"\b(19\d{2}|20\d{2})\b", x)
        if m:
            y = int(m.group(1))
            return y if 1900 <= y <= 2100 else None
    return None


def _coerce_rating(x: Any) -> Optional[float]:
    try:
        v = float(x)
        if 0.0 <= v <= 10.0:
            return v
    except Exception:
        return None
    return None


def _dedup_join(names: List[str]) -> Optional[str]:
    if not names:
        return None
    seen = set()
    out = []
    for n in names:
        if n and n not in seen:
            seen.add(n)
            out.append(n)
    return ", ".join(out) if out else None


def _parse_ld_json(ld_obj: Any) -> Dict[str, Any]:
    out: Dict[str, Any] = {}

    if isinstance(ld_obj, list):
        for item in ld_obj:
            if isinstance(item, dict):
                tmp = _parse_ld_json(item)
                for k, v in tmp.items():
                    if v and not out.get(k):
                        out[k] = v
        return out

    if not isinstance(ld_obj, dict):
        return out

    desc = _first_str(ld_obj.get("description"))
    if desc:
        out["summary"] = desc

    dp = ld_obj.get("datePublished") or ld_obj.get("dateCreated")
    y = _coerce_year(dp)
    if y:
        out["year"] = y

    actors = ld_obj.get("actor") or ld_obj.get("actors")
    cast_names: List[str] = []
    if isinstance(actors, list):
        for a in actors:
            if isinstance(a, dict):
                n = _first_str(a.get("name"))
                if n:
                    cast_names.append(n)
            elif isinstance(a, str) and a.strip():
                cast_names.append(a.strip())
    elif isinstance(actors, dict):
        n = _first_str(actors.get("name"))
        if n:
            cast_names.append(n)

    cast_out = _dedup_join(cast_names)
    if cast_out:
        out["starring"] = cast_out

    director = ld_obj.get("director")
    dir_names: List[str] = []
    if isinstance(director, list):
        for d in director:
            if isinstance(d, dict):
                n = _first_str(d.get("name"))
                if n:
                    dir_names.append(n)
            elif isinstance(d, str) and d.strip():
                dir_names.append(d.strip())
    elif isinstance(director, dict):
        n = _first_str(director.get("name"))
        if n:
            dir_names.append(n)
    elif isinstance(director, str) and director.strip():
        dir_names.append(director.strip())

    dir_out = _dedup_join(dir_names)
    if dir_out:
        out["director"] = dir_out

    agg = ld_obj.get("aggregateRating") or {}
    if isinstance(agg, dict):
        rv = agg.get("ratingValue")
        r = _coerce_rating(rv)
        if r is not None:
            out["rating"] = r

    return out


def _walk_dicts(obj: Any) -> List[dict]:
    found: List[dict] = []
    if isinstance(obj, dict):
        found.append(obj)
        for v in obj.values():
            found.extend(_walk_dicts(v))
    elif isinstance(obj, list):
        for v in obj:
            found.extend(_walk_dicts(v))
    return found


def _extract_from_candidate_dict(c: dict) -> Dict[str, Any]:
    out: Dict[str, Any] = {}

    out["summary"] = _first_str(c.get("summary") or c.get("description") or c.get("synopsis"))
    out["year"] = _coerce_year(c.get("year") or c.get("releaseYear") or c.get("datePublished"))
    out["rating"] = _coerce_rating(c.get("rating") or c.get("score") or c.get("ratingValue"))

    cast = c.get("starring") or c.get("cast") or c.get("actors")
    cast_names: List[str] = []
    if isinstance(cast, list):
        for a in cast:
            if isinstance(a, dict):
                n = _first_str(a.get("name"))
                if n:
                    cast_names.append(n)
            elif isinstance(a, str) and a.strip():
                cast_names.append(a.strip())
    elif isinstance(cast, dict):
        n = _first_str(cast.get("name"))
        if n:
            cast_names.append(n)
    elif isinstance(cast, str) and cast.strip():
        cast_names.append(cast.strip())
    cast_out = _dedup_join(cast_names)
    if cast_out:
        out["starring"] = cast_out

    d = c.get("director")
    dir_names: List[str] = []
    if isinstance(d, list):
        for x in d:
            if isinstance(x, dict):
                n = _first_str(x.get("name"))
                if n:
                    dir_names.append(n)
            elif isinstance(x, str) and x.strip():
                dir_names.append(x.strip())
    elif isinstance(d, dict):
        n = _first_str(d.get("name"))
        if n:
            dir_names.append(n)
    elif isinstance(d, str) and d.strip():
        dir_names.append(d.strip())

    dir_out = _dedup_join(dir_names)
    if dir_out:
        out["director"] = dir_out

    return {k: v for k, v in out.items() if v is not None}


# ---- MOTN scraping
async def scrape_search_motn(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    q = query.strip()
    if not q:
        return []

    results: List[Dict[str, Any]] = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(f"{MOTN_BASE_URL}/browse", wait_until="domcontentloaded")
            await page.wait_for_timeout(800)

            inputs = await page.query_selector_all("input")
            if inputs:
                await inputs[0].fill(q)
                await page.wait_for_timeout(1200)

            links = await page.query_selector_all('a[href*="/show/"], a[href*="/shows/"]')
            for a in links[: limit * 3]:
                href = (await a.get_attribute("href")) or ""
                if "/show" not in href and "/shows" not in href:
                    continue
                full_url = href if href.startswith("http") else (MOTN_BASE_URL + href)
                text = ((await a.inner_text()) or "").strip()
                results.append({"title": text if text else None, "motn_url": full_url})

        except PlaywrightTimeoutError:
            pass
        finally:
            await browser.close()

    seen = set()
    dedup = []
    for r in results:
        u = r.get("motn_url")
        if u and u not in seen:
            seen.add(u)
            dedup.append(r)
    return dedup[:limit]


async def scrape_details_from_show_page(motn_url: str) -> Dict[str, Any]:
    if not motn_url:
        return {}

    show_id = _extract_id_from_motn_url(motn_url)
    captured_payloads: List[dict] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        async def on_response(resp):
            try:
                ct = (resp.headers.get("content-type") or "").lower()
                if "application/json" in ct:
                    data = await resp.json()
                    if isinstance(data, dict):
                        captured_payloads.append(data)
            except Exception:
                pass

        page.on("response", on_response)

        try:
            await page.goto(motn_url, wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)

            out: Dict[str, Any] = {}

            # (1) JSON-LD
            try:
                ld_scripts = await page.query_selector_all('script[type="application/ld+json"]')
                for s in ld_scripts:
                    raw = ((await s.inner_text()) or "").strip()
                    if not raw:
                        continue
                    try:
                        ld_obj = json.loads(raw)
                        ld_out = _parse_ld_json(ld_obj)
                        for k, v in ld_out.items():
                            if v is not None and not out.get(k):
                                out[k] = v
                    except Exception:
                        continue
            except Exception:
                pass

            # (2) XHR payloads
            candidates: List[dict] = []
            for payload in captured_payloads:
                candidates.extend(_walk_dicts(payload))

            best: Optional[dict] = None
            for c in candidates:
                if not isinstance(c, dict):
                    continue
                if show_id and (str(c.get("id")) == str(show_id) or str(c.get("show_id")) == str(show_id)):
                    best = c
                    break
                keys = set(c.keys())
                if ("summary" in keys or "synopsis" in keys or "description" in keys) and ("title" in keys or "name" in keys):
                    best = c

            if best:
                mapped = _extract_from_candidate_dict(best)
                for k, v in mapped.items():
                    if v is not None and not out.get(k):
                        out[k] = v

            # (3) meta description fallback
            if not out.get("summary"):
                try:
                    md = await page.query_selector('meta[name="description"]')
                    if md:
                        desc = await md.get_attribute("content")
                        if desc and len(desc.strip()) >= 20:
                            out["summary"] = desc.strip()
                except Exception:
                    pass

            return out

        finally:
            await browser.close()


# ---- Movies tools (UPDATED: include_details option)
@mcp.tool()
def search_movie(title: str, limit: int = 10, include_details: bool = False) -> List[Dict[str, Any]]:
    """
    Cache-first movie search:
      1) Search in CSV KB
      2) If none: scrape MOTN search, add minimal rows (title + motn_url + internal_id if needed)
    If include_details=True, includes summary/starring/director/rating FROM CSV ONLY (no scraping here).
    """
    global MOVIES_DF, MOV_COL_ID

    q = _normalize_text(title)
    if not q:
        return []

    def _row_to_out(row: pd.Series) -> Dict[str, Any]:
        base = {
            "id": _safe_int(row.get(MOV_COL_ID)) if MOV_COL_ID else _safe_int(row.get("internal_id")),
            "title": _safe_str(row.get(MOV_COL_TITLE)),
            "year": _safe_int(row.get("year")) or (_safe_int(row.get(MOV_COL_YEAR_LEGACY)) if MOV_COL_YEAR_LEGACY else None),
            "motn_url": _safe_str(row.get("motn_url")),
        }
        if include_details:
            base.update({
                "summary": _safe_str(row.get("summary")),
                "starring": _safe_str(row.get("starring")),
                "director": _safe_str(row.get("director")),
                "rating": _safe_float(row.get("rating")),
            })
        return base

    # 1) local search
    hits = MOVIES_DF[MOVIES_DF["_title_norm"].str.contains(re.escape(q), na=False)].copy()
    if not hits.empty:
        out = []
        for _, row in hits.head(max(1, int(limit))).iterrows():
            out.append(_row_to_out(row))
        return out

    # 2) fallback scraping
    scraped = asyncio.run(scrape_search_motn(title, limit=limit))
    if not scraped:
        return []

    # ensure an ID column
    if MOV_COL_ID is None or MOV_COL_ID not in MOVIES_DF.columns:
        if "internal_id" not in MOVIES_DF.columns:
            MOVIES_DF["internal_id"] = range(1, len(MOVIES_DF) + 1)
        id_col = "internal_id"
        MOV_COL_ID = "internal_id"
    else:
        id_col = MOV_COL_ID

    next_id = int(MOVIES_DF[id_col].max()) + 1 if len(MOVIES_DF) and MOVIES_DF[id_col].notna().any() else 1

    new_rows = []
    for r in scraped:
        new_title = r.get("title") or title
        new_url = r.get("motn_url")

        if new_url and (MOVIES_DF["motn_url"] == new_url).any():
            continue

        row = {c: None for c in MOVIES_DF.columns}
        row[MOV_COL_TITLE] = new_title
        row["_title_norm"] = _normalize_text(new_title)
        row["motn_url"] = new_url
        row[id_col] = next_id

        row["summary"] = None
        row["starring"] = None
        row["director"] = None
        row["year"] = None
        row["rating"] = None
        row["rating_last_updated_at"] = None
        row["details_last_updated_at"] = None

        next_id += 1
        new_rows.append(row)

    if new_rows:
        MOVIES_DF = pd.concat([MOVIES_DF, pd.DataFrame(new_rows)], ignore_index=True)
        _persist_movies_df()

    # return now
    hits2 = MOVIES_DF[MOVIES_DF["_title_norm"].str.contains(re.escape(q), na=False)].copy()
    out = []
    for _, row in hits2.head(max(1, int(limit))).iterrows():
        out.append(_row_to_out(row))
    return out


@mcp.tool()
def get_movie(movie_id: int) -> Dict[str, Any]:
    """
    Returns a movie from CSV KB.
    If missing/stale: scrapes MOTN show page ONCE and updates:
      - summary (synopsis)
      - starring (cast)
      - director
      - year
      - rating
    """
    global MOVIES_DF

    if movie_id is None:
        return {"found": False, "error": "movie_id is required"}

    if MOV_COL_ID and MOV_COL_ID in MOVIES_DF.columns:
        id_col = MOV_COL_ID
    elif "internal_id" in MOVIES_DF.columns:
        id_col = "internal_id"
    else:
        return {"found": False, "error": "No id column in movies CSV"}

    rows = MOVIES_DF.loc[MOVIES_DF[id_col] == movie_id]
    if rows.empty:
        return {"found": False, "movie_id": movie_id}

    idx = rows.index[0]
    row = MOVIES_DF.loc[idx]

    motn_url = _safe_str(row.get("motn_url"))

    rating_last = _parse_ts(row.get("rating_last_updated_at"))
    details_last = _parse_ts(row.get("details_last_updated_at"))

    rating_stale = (rating_last is None) or (_now_ts() - rating_last > MOVIES_RATING_TTL_SECONDS)
    details_stale = (details_last is None) or (_now_ts() - details_last > MOVIES_DETAILS_TTL_SECONDS)

    missing_summary = _safe_str(row.get("summary")) is None
    missing_starring = _safe_str(row.get("starring")) is None
    missing_director = _safe_str(row.get("director")) is None
    missing_year = _safe_int(row.get("year")) is None

    need_details = bool(motn_url) and (details_stale or missing_summary or missing_starring or missing_director or missing_year)
    need_rating = bool(motn_url) and rating_stale

    details_refreshed = False
    rating_refreshed = False

    if motn_url and (need_details or need_rating):
        scraped: Dict[str, Any] = {}
        try:
            scraped = asyncio.run(scrape_details_from_show_page(motn_url))
        except Exception:
            scraped = {}

        if need_details and scraped:
            y = scraped.get("year")
            s = scraped.get("summary")
            cast = scraped.get("starring")
            d = scraped.get("director")

            if y is not None:
                MOVIES_DF.at[idx, "year"] = int(y)
            if s:
                MOVIES_DF.at[idx, "summary"] = s
            if cast:
                MOVIES_DF.at[idx, "starring"] = cast
            if d:
                MOVIES_DF.at[idx, "director"] = d

            MOVIES_DF.at[idx, "details_last_updated_at"] = _now_ts()
            details_refreshed = True

        if need_rating and scraped:
            r = scraped.get("rating")
            if r is not None:
                MOVIES_DF.at[idx, "rating"] = float(r)
                MOVIES_DF.at[idx, "rating_last_updated_at"] = _now_ts()
                rating_refreshed = True

        if details_refreshed or rating_refreshed:
            _persist_movies_df()

    row2 = MOVIES_DF.loc[idx]
    return {
        "found": True,
        "id": _safe_int(row2.get(id_col)),
        "title": _safe_str(row2.get(MOV_COL_TITLE)),
        "year": _safe_int(row2.get("year")) or (_safe_int(row2.get(MOV_COL_YEAR_LEGACY)) if MOV_COL_YEAR_LEGACY else None),
        "summary": _safe_str(row2.get("summary")),
        "starring": _safe_str(row2.get("starring")),
        "director": _safe_str(row2.get("director")),
        "motn_url": _safe_str(row2.get("motn_url")),
        "rating": _safe_float(row2.get("rating")),
        "rating_last_updated_at": row2.get("rating_last_updated_at"),
        "details_last_updated_at": row2.get("details_last_updated_at"),
        "details_refreshed": details_refreshed,
        "rating_refreshed": rating_refreshed,
    }


# ============================================================
# PART B — CINEFIL SHOWTIMES (robust cinema names + grouped output)
# ============================================================
CINEFIL_CACHE_DIR = os.getenv("CINEFIL_SHOWTIMES_CACHE_DIR", "data/cinefil_showtimes_cache")
CINEFIL_CACHE_TTL_SECONDS = int(os.getenv("CINEFIL_SHOWTIMES_TTL_SECONDS", str(2 * 3600)))  # 2h
CINEFIL_MAJOR_CITIES = ["Paris", "Marseille", "Lyon", "Bordeaux", "Lille"]

CINEFIL_DAY_RE = re.compile(r"\b(Lun\.|Mar\.|Mer\.|Jeu\.|Ven\.|Sam\.|Dim\.)\s*(\d{1,2})\b")
CINEFIL_TIME_RE = re.compile(r"\b(\d{1,2}:\d{2})\b")
CINEFIL_LANG_RE = re.compile(r"^(VF|VOSTFR|VO|VOST|3D|IMAX)$", re.IGNORECASE)


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _slugify_city(s: str) -> str:
    s = s.strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s).strip("-")
    return s


def _cinefil_cache_key(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def _cinefil_cache_path(key: str) -> str:
    return os.path.join(CINEFIL_CACHE_DIR, f"{key}.json")


def _cinefil_load_cache(url: str) -> Optional[Dict[str, Any]]:
    key = _cinefil_cache_key(url)
    path = _cinefil_cache_path(key)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        if _now_ts() - int(payload.get("_cached_at", 0)) > CINEFIL_CACHE_TTL_SECONDS:
            return None
        return payload
    except Exception:
        return None


def _cinefil_save_cache(url: str, payload: Dict[str, Any]) -> None:
    _ensure_dir(CINEFIL_CACHE_DIR)
    payload["_cached_at"] = _now_ts()
    with open(_cinefil_cache_path(_cinefil_cache_key(url)), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def _cinefil_build_city_url(film_seances_url: str, city: str) -> str:
    base = film_seances_url.rstrip("/")
    if city.strip().lower() == "paris":
        return base
    return f"{base}/{_slugify_city(city)}?og_search=1"


def _cinefil_clean_text(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"\s+", " ", s)
    return s


def _cinefil_get_heading_text(h: Tag) -> str:
    if h is None:
        return ""
    a = h.find("a")
    if a:
        t = _cinefil_clean_text(a.get_text(" ", strip=True))
        if t:
            return t
    return _cinefil_clean_text(h.get_text(" ", strip=True))


def _cinefil_extract_city_from_page(soup: BeautifulSoup) -> str:
    for h2 in soup.find_all(["h2", "h3"]):
        txt = h2.get_text(" ", strip=True)
        m = re.search(r"Les séances à\s+(.+)", txt)
        if m:
            return m.group(1).strip()
    return "Unknown"


def _cinefil_iter_cinema_headings(soup: BeautifulSoup) -> List[Tag]:
    anchor = None
    for h2 in soup.find_all(["h2", "h3"]):
        if "Les séances à" in h2.get_text(" ", strip=True):
            anchor = h2
            break
    if not anchor:
        return soup.find_all(["h3", "h4"])

    nodes: List[Tag] = []
    cur = anchor.next_sibling
    while cur:
        if isinstance(cur, Tag):
            txt = cur.get_text(" ", strip=True)
            if txt.startswith("Séances à proximité") or txt.startswith("Autres villes"):
                break
            nodes.append(cur)
        cur = cur.next_sibling

    headings: List[Tag] = []
    for n in nodes:
        headings.extend(n.find_all(["h3", "h4"]))
    return headings


def _cinefil_collect_block_lines_from_heading(h: Tag) -> List[str]:
    lines: List[str] = []
    cur = h
    while cur:
        if isinstance(cur, Tag):
            if cur is not h and cur.name in ("h3", "h4"):
                break
            t = cur.get_text("\n", strip=True)
            if t:
                for l in t.split("\n"):
                    ll = l.strip()
                    if ll:
                        lines.append(ll)
        cur = cur.next_sibling
    return lines


def _cinefil_parse_days_and_rows(block_text_lines: List[str]) -> Tuple[List[str], List[List[Dict[str, Optional[str]]]]]:
    day_line_idx = None
    for i, line in enumerate(block_text_lines):
        if len(CINEFIL_DAY_RE.findall(line)) >= 2:
            day_line_idx = i
            break
    if day_line_idx is None:
        return [], []

    days = [f"{d} {n}" for (d, n) in CINEFIL_DAY_RE.findall(block_text_lines[day_line_idx])]

    rows: List[List[Dict[str, Optional[str]]]] = []
    cursor = day_line_idx + 1
    candidates: List[str] = []

    while cursor < len(block_text_lines) and len(candidates) < len(days):
        l = block_text_lines[cursor].strip()
        cursor += 1
        if not l:
            continue
        if "Voir les tarifs" in l:
            continue
        candidates.append(l)

    for line in candidates:
        parts = line.split()
        out: List[Dict[str, Optional[str]]] = []
        j = 0
        while j < len(parts):
            p = parts[j]
            if CINEFIL_TIME_RE.match(p):
                tag = None
                if j + 1 < len(parts) and CINEFIL_LANG_RE.match(parts[j + 1]):
                    tag = parts[j + 1].upper()
                    j += 1
                out.append({"time": p, "tag": tag})
            j += 1

        if "Aucune" in line and "séance" in line and not out:
            rows.append([])
        else:
            rows.append(out)

    if len(rows) != len(days):
        return days, [r for r in rows]
    return days, rows


async def _cinefil_fetch_html(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121 Safari/537.36",
        "Accept-Language": "fr-FR,fr;q=0.9",
    }
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, headers=headers) as client:
        r = await client.get(url)
        r.raise_for_status()
        return r.text


async def _cinefil_scrape_city(film_seances_url: str, city: str, limit_cinemas: int = 10) -> Dict[str, Any]:
    url = _cinefil_build_city_url(film_seances_url, city)

    cached = _cinefil_load_cache(url)
    if cached:
        return cached

    html = await _cinefil_fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")

    film_title = (soup.find("h1").get_text(" ", strip=True) if soup.find("h1") else None)
    page_city = _cinefil_extract_city_from_page(soup)
    city_label = page_city if page_city != "Unknown" else city

    headings = _cinefil_iter_cinema_headings(soup)

    cinemas_out: List[Dict[str, Any]] = []
    used = 0

    for h in headings:
        if used >= max(1, limit_cinemas):
            break

        cinema_name = _cinefil_get_heading_text(h)
        if not cinema_name or cinema_name.lower().startswith("séances"):
            continue

        lines = _cinefil_collect_block_lines_from_heading(h)
        days, rows = _cinefil_parse_days_and_rows(lines)
        if not days:
            continue

        day_items = []
        for idx, day_label in enumerate(days):
            times = rows[idx] if idx < len(rows) else []
            day_items.append({"day_label": day_label, "times": times})

        cinemas_out.append({"city": city_label, "cinema": cinema_name, "days": day_items})
        used += 1

    payload = {
        "source": "cinefil.com",
        "film_title": film_title,
        "city": city_label,
        "source_url": url,
        "cinemas": cinemas_out,
    }
    _cinefil_save_cache(url, payload)
    return payload


@mcp.tool()
def cinefil_showtimes(
    film_seances_url: str,
    city: Optional[str] = None,
    major_cities: bool = True,
    limit_cinemas_per_city: int = 10
) -> Dict[str, Any]:
    if not film_seances_url.startswith("http"):
        return {"error": "film_seances_url must be a full URL (https://...)"}

    async def _run() -> Dict[str, Any]:
        cities = [city] if city else (CINEFIL_MAJOR_CITIES if major_cities else ["Paris"])
        out: Dict[str, Any] = {
            "film_seances_url": film_seances_url,
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "cities": [],
        }

        for c in cities:
            res = await _cinefil_scrape_city(
                film_seances_url=film_seances_url,
                city=c,
                limit_cinemas=limit_cinemas_per_city,
            )
            out["cities"].append(res)

        return out

    return asyncio.run(_run())


# ============================================================
# Main
# ============================================================
if __name__ == "__main__":
    print(f"[OK] Movies CSV: {MOVIES_CSV_PATH} | rows={len(MOVIES_DF)}")
    print("[OK] MCP tools: search_movie, get_movie, cinefil_showtimes")
    mcp.run()