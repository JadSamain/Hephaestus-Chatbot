# server_mcp_cache_refresh.py
# ------------------------------------------------------------
# MCP server (FastMCP) that serves movies from a CSV "KB" (cache-first)
# and falls back to live Playwright scraping on MovieOfTheNight when:
#  - movie not found locally (search fallback)
#  - movie details missing or stale (synopsis, cast, year, rating)
#
# Tools exposed (ONLY 2):
#   - search_movie(title: str, limit: int = 10) -> list
#   - get_movie(movie_id: int) -> dict
#
# Run:
#   pip install mcp pandas playwright
#   playwright install
#   export MOVIES_CSV_PATH="data/movies_catalog_fr.csv"
#   python server_mcp_cache_refresh.py
# ------------------------------------------------------------

from __future__ import annotations

import os
import re
import json
import time
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime
from urllib.parse import urlparse, parse_qs

import pandas as pd
from mcp.server.fastmcp import FastMCP
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# -----------------------------
# Config
# -----------------------------
mcp = FastMCP("hephaestus-movies-cache-refresh")

CSV_PATH = os.getenv("MOVIES_CSV_PATH", "data/movies_catalog_fr.csv")
BASE_URL = "https://www.movieofthenight.com"

# Freshness
RATING_TTL_SECONDS = int(os.getenv("RATING_TTL_SECONDS", str(24 * 3600)))           # 24h
DETAILS_TTL_SECONDS = int(os.getenv("DETAILS_TTL_SECONDS", str(30 * 24 * 3600)))   # 30j (details bougent rarement)

# Simple file lock for CSV writes (proto-safe)
WRITE_LOCK_PATH = os.getenv("CSV_LOCK_PATH", CSV_PATH + ".lock")


# -----------------------------
# Utils
# -----------------------------
def now_ts() -> int:
    return int(time.time())


def normalize_text(s: Any) -> str:
    s = "" if s is None else str(s)
    s = s.strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def safe_int(x: Any) -> Optional[int]:
    try:
        if pd.isna(x):
            return None
        return int(float(x))
    except Exception:
        return None


def safe_float(x: Any) -> Optional[float]:
    try:
        if pd.isna(x):
            return None
        return float(x)
    except Exception:
        return None


def safe_str(x: Any) -> Optional[str]:
    if x is None:
        return None
    try:
        if pd.isna(x):
            return None
    except Exception:
        pass
    s = str(x).strip()
    return s if s else None


def pick_col(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    for c in candidates:
        if c in df.columns:
            return c
    return None


def parse_ts(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        if isinstance(value, float) and pd.isna(value):
            return None
    except Exception:
        pass

    # unix int/float as str
    try:
        return int(float(value))
    except Exception:
        pass

    # ISO
    try:
        return int(datetime.fromisoformat(str(value)).timestamp())
    except Exception:
        return None


def ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds required columns if missing (without breaking existing CSV).
    """
    required = {
        "motn_url": None,

        # Details
        "summary": None,
        "starring": None,  # store as a string: "Actor A, Actor B, ..."
        "director": None,
        "year": None,

        # Rating & freshness
        "rating": None,
        "rating_last_updated_at": None,   # unix ts
        "details_last_updated_at": None,  # unix ts
    }
    for col, default in required.items():
        if col not in df.columns:
            df[col] = default
    return df


def acquire_file_lock(lock_path: str, timeout: int = 10) -> None:
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


def release_file_lock(lock_path: str) -> None:
    try:
        os.remove(lock_path)
    except FileNotFoundError:
        pass


def atomic_write_csv(df: pd.DataFrame, path: str) -> None:
    tmp = path + ".tmp"
    df.to_csv(tmp, index=False)
    os.replace(tmp, path)


# -----------------------------
# Global CSV store (KB)
# -----------------------------
if not os.path.exists(CSV_PATH):
    raise FileNotFoundError(f"CSV not found: {CSV_PATH}")

DF = pd.read_csv(CSV_PATH)
DF = ensure_columns(DF)

COL_ID = pick_col(DF, ["show_id", "id", "movie_id", "ID", "internal_id"])
COL_TITLE = pick_col(DF, ["title", "Titre", "name", "Name"])
COL_YEAR_LEGACY = pick_col(DF, ["year", "Year", "annee", "Année"])  # if your CSV already had a year column

if COL_TITLE is None:
    raise ValueError("No title column found in CSV (expected title/Titre/name/Name).")

if "_title_norm" not in DF.columns:
    DF["_title_norm"] = DF[COL_TITLE].astype(str).map(normalize_text)


def persist_df() -> None:
    global DF
    acquire_file_lock(WRITE_LOCK_PATH)
    try:
        atomic_write_csv(DF, CSV_PATH)
    finally:
        release_file_lock(WRITE_LOCK_PATH)


# -----------------------------
# Scraping helpers
# -----------------------------
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
    """
    Normalize JSON-LD (schema.org) blocks into our fields.
    """
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
    out_cast = _dedup_join(cast_names)
    if out_cast:
        out["starring"] = out_cast

    director = ld_obj.get("director")
    directors: List[str] = []
    if isinstance(director, list):
        for d in director:
            if isinstance(d, dict):
                n = _first_str(d.get("name"))
                if n:
                    directors.append(n)
            elif isinstance(d, str) and d.strip():
                directors.append(d.strip())
    elif isinstance(director, dict):
        n = _first_str(director.get("name"))
        if n:
            directors.append(n)
    elif isinstance(director, str) and director.strip():
        directors.append(director.strip())
    out_dir = _dedup_join(directors)
    if out_dir:
        out["director"] = out_dir

    agg = ld_obj.get("aggregateRating") or {}
    if isinstance(agg, dict):
        rv = agg.get("ratingValue")
        r = _coerce_rating(rv)
        if r is not None:
            out["rating"] = r

    return out


def _walk_dicts(obj: Any) -> List[dict]:
    """Collect all dicts from nested JSON payload."""
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
    """
    Try to map a candidate dict (from captured JSON) to our fields.
    """
    out: Dict[str, Any] = {}

    # summary
    out["summary"] = _first_str(c.get("summary") or c.get("description") or c.get("synopsis"))

    # year
    out["year"] = _coerce_year(c.get("year") or c.get("releaseYear") or c.get("datePublished"))

    # rating
    out["rating"] = _coerce_rating(c.get("rating") or c.get("score") or c.get("ratingValue"))

    # starring / cast / actors
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
        # might already be "A, B, C"
        cast_names.append(cast.strip())
    out_cast = _dedup_join(cast_names)
    if out_cast:
        out["starring"] = out_cast

    # director
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
    out_dir = _dedup_join(dir_names)
    if out_dir:
        out["director"] = out_dir

    # Remove empties
    return {k: v for k, v in out.items() if v is not None}


# -----------------------------
# Scraping (Playwright)
# -----------------------------
async def scrape_search_motn(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Search a title on MovieOfTheNight (SPA). Generic approach:
      - open /browse
      - fill first input
      - collect show links
    NOTE: If you already have stable selectors from your old scraper, plug them here.
    """
    q = query.strip()
    if not q:
        return []

    results: List[Dict[str, Any]] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(f"{BASE_URL}/browse", wait_until="domcontentloaded")
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

                full_url = href if href.startswith("http") else (BASE_URL + href)
                text = ((await a.inner_text()) or "").strip()
                title_guess = text if text else None

                results.append({"title": title_guess, "motn_url": full_url})

        except PlaywrightTimeoutError:
            pass
        finally:
            await browser.close()

    # dedup by URL
    seen = set()
    dedup = []
    for r in results:
        u = r.get("motn_url")
        if u and u not in seen:
            seen.add(u)
            dedup.append(r)
    return dedup[:limit]


async def scrape_details_from_show_page(motn_url: str) -> Dict[str, Any]:
    """
    Robust details scraping for a MOTN show page (SPA):
      1) JSON-LD (script[type="application/ld+json"])
      2) Capture JSON XHR responses during load and parse nested dict candidates
      3) Fallback to meta description if summary missing
    Returns: summary, starring, director, year, rating
    """
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
            # let XHR settle
            await page.wait_for_timeout(2000)

            out: Dict[str, Any] = {}

            # (1) JSON-LD
            try:
                ld_scripts = await page.query_selector_all('script[type="application/ld+json"]')
                for s in ld_scripts:
                    raw = (await s.inner_text()) or ""
                    raw = raw.strip()
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

            # (2) XHR JSON payloads
            candidates: List[dict] = []
            for payload in captured_payloads:
                candidates.extend(_walk_dicts(payload))

            best: Optional[dict] = None
            for c in candidates:
                if not isinstance(c, dict):
                    continue

                # match by id if possible
                if show_id and (str(c.get("id")) == str(show_id) or str(c.get("show_id")) == str(show_id)):
                    best = c
                    break

                # heuristic: looks like a show object
                keys = set(c.keys())
                if ("summary" in keys or "synopsis" in keys or "description" in keys) and ("title" in keys or "name" in keys):
                    best = c

            if best:
                mapped = _extract_from_candidate_dict(best)
                for k, v in mapped.items():
                    if v is not None and not out.get(k):
                        out[k] = v

            # (3) fallback meta description for summary
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


# -----------------------------
# MCP Tools (2 tools only)
# -----------------------------
@mcp.tool()
def search_movie(title: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Cache-first:
      1) search in CSV
      2) if none -> scrape MOTN search, add minimal rows to CSV (title + motn_url + id), return
    """
    global DF

    q = normalize_text(title)
    if not q:
        return []

    # 1) Local
    hits = DF[DF["_title_norm"].str.contains(re.escape(q), na=False)].copy()
    if not hits.empty:
        out = []
        for _, row in hits.head(max(1, int(limit))).iterrows():
            out.append({
                "id": safe_int(row.get(COL_ID)) if COL_ID else safe_int(row.get("internal_id")),
                "title": safe_str(row.get(COL_TITLE)),
                "year": safe_int(row.get("year")) or (safe_int(row.get(COL_YEAR_LEGACY)) if COL_YEAR_LEGACY else None),
                "motn_url": safe_str(row.get("motn_url")),
            })
        return out

    # 2) Fallback web search
    scraped = asyncio.run(scrape_search_motn(title, limit=limit))
    if not scraped:
        return []

    # Ensure a local id column
    if COL_ID is None or COL_ID not in DF.columns:
        if "internal_id" not in DF.columns:
            DF["internal_id"] = range(1, len(DF) + 1)
        id_col = "internal_id"
    else:
        id_col = COL_ID

    next_id = int(DF[id_col].max()) + 1 if len(DF) and DF[id_col].notna().any() else 1

    new_rows = []
    for r in scraped:
        new_title = r.get("title") or title
        new_url = r.get("motn_url")

        if new_url and (DF["motn_url"] == new_url).any():
            continue

        row = {c: None for c in DF.columns}
        row[COL_TITLE] = new_title
        row["_title_norm"] = normalize_text(new_title)
        row["motn_url"] = new_url
        row[id_col] = next_id

        # leave details empty (filled by get_movie)
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
        DF = pd.concat([DF, pd.DataFrame(new_rows)], ignore_index=True)
        persist_df()

    # return local now
    hits2 = DF[DF["_title_norm"].str.contains(re.escape(q), na=False)].copy()
    out = []
    for _, row in hits2.head(max(1, int(limit))).iterrows():
        out.append({
            "id": safe_int(row.get(COL_ID)) if COL_ID else safe_int(row.get("internal_id")),
            "title": safe_str(row.get(COL_TITLE)),
            "year": safe_int(row.get("year")) or (safe_int(row.get(COL_YEAR_LEGACY)) if COL_YEAR_LEGACY else None),
            "motn_url": safe_str(row.get("motn_url")),
        })
    return out


@mcp.tool()
def get_movie(movie_id: int) -> Dict[str, Any]:
    """
    Returns a movie from the CSV.
    If missing/stale fields, scrapes the show page ONCE and updates:
      - summary (synopsis)
      - starring (cast list)
      - director
      - year
      - rating (with TTL)
    """
    global DF

    if movie_id is None:
        return {"found": False, "error": "movie_id is required"}

    # Determine ID column
    if COL_ID and COL_ID in DF.columns:
        id_col = COL_ID
    elif "internal_id" in DF.columns:
        id_col = "internal_id"
    else:
        return {"found": False, "error": "No id column in CSV"}

    rows = DF.loc[DF[id_col] == movie_id]
    if rows.empty:
        return {"found": False, "movie_id": movie_id}

    idx = rows.index[0]
    row = DF.loc[idx]

    motn_url = safe_str(row.get("motn_url"))

    # Freshness
    rating_last = parse_ts(row.get("rating_last_updated_at"))
    details_last = parse_ts(row.get("details_last_updated_at"))

    rating_stale = (rating_last is None) or (now_ts() - rating_last > RATING_TTL_SECONDS)
    details_stale = (details_last is None) or (now_ts() - details_last > DETAILS_TTL_SECONDS)

    # Missing fields?
    missing_summary = safe_str(row.get("summary")) is None
    missing_starring = safe_str(row.get("starring")) is None
    missing_director = safe_str(row.get("director")) is None
    missing_year = safe_int(row.get("year")) is None

    need_details = bool(motn_url) and (details_stale or missing_summary or missing_starring or missing_director or missing_year)
    need_rating = bool(motn_url) and rating_stale

    refreshed_details = False
    refreshed_rating = False

    # Scrape ONCE if needed
    if motn_url and (need_details or need_rating):
        scraped = {}
        try:
            scraped = asyncio.run(scrape_details_from_show_page(motn_url))
        except Exception:
            scraped = {}

        # Update details
        if need_details and scraped:
            y = scraped.get("year")
            s = scraped.get("summary")
            cast = scraped.get("starring")
            d = scraped.get("director")

            if y is not None:
                DF.at[idx, "year"] = int(y)
            if s:
                DF.at[idx, "summary"] = s
            if cast:
                DF.at[idx, "starring"] = cast
            if d:
                DF.at[idx, "director"] = d

            DF.at[idx, "details_last_updated_at"] = now_ts()
            refreshed_details = True

        # Update rating (only if stale)
        if need_rating and scraped:
            r = scraped.get("rating")
            if r is not None:
                DF.at[idx, "rating"] = float(r)
                DF.at[idx, "rating_last_updated_at"] = now_ts()
                refreshed_rating = True

        if refreshed_details or refreshed_rating:
            persist_df()

    # Return latest row
    row2 = DF.loc[idx]
    return {
        "found": True,
        "id": safe_int(row2.get(id_col)),
        "title": safe_str(row2.get(COL_TITLE)),
        "year": safe_int(row2.get("year")) or (safe_int(row2.get(COL_YEAR_LEGACY)) if COL_YEAR_LEGACY else None),
        "summary": safe_str(row2.get("summary")),
        "starring": safe_str(row2.get("starring")),
        "director": safe_str(row2.get("director")),
        "motn_url": safe_str(row2.get("motn_url")),
        "rating": safe_float(row2.get("rating")),
        "rating_last_updated_at": row2.get("rating_last_updated_at"),
        "details_last_updated_at": row2.get("details_last_updated_at"),
        "details_refreshed": refreshed_details,
        "rating_refreshed": refreshed_rating,
    }


# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    print(f"[OK] Loaded CSV: {CSV_PATH} | rows={len(DF)}")
    print(f"[OK] TTL rating={RATING_TTL_SECONDS}s | details={DETAILS_TTL_SECONDS}s")
    print("[OK] MCP tools: search_movie, get_movie")
    mcp.run()
