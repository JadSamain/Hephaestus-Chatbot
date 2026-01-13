from __future__ import annotations

import os
import re
import json
import time
import asyncio
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timezone

import pandas as pd
from mcp.server.fastmcp import FastMCP

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# -----------------------------
# Config
# -----------------------------
mcp = FastMCP("hephaestus-movies-cache-refresh")

CSV_PATH = os.getenv("MOVIES_CSV_PATH", "data/movies_catalog_fr.csv")
RATING_TTL_SECONDS = int(os.getenv("RATING_TTL_SECONDS", str(24 * 3600)))  # 24h par défaut
BASE_URL = "https://www.movieofthenight.com"

# Pour éviter des écritures concurrentes “bêtes” sur le CSV
WRITE_LOCK_PATH = os.getenv("CSV_LOCK_PATH", CSV_PATH + ".lock")

# -----------------------------
# Utils
# -----------------------------
def now_ts() -> int:
    return int(time.time())

def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()

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

def ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Ajoute les colonnes nécessaires si absentes."""
    required = {
        "motn_url": None,
        "rating_last_updated_at": None,   # timestamp unix int ou string, au choix
        "rating": None,
    }
    for col, default in required.items():
        if col not in df.columns:
            df[col] = default
    return df

def acquire_file_lock(lock_path: str, timeout: int = 10) -> None:
    """Lock ultra-simple via fichier. (OK pour un proto mono-machine.)"""
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
# Global CSV store
# -----------------------------
if not os.path.exists(CSV_PATH):
    raise FileNotFoundError(f"CSV not found: {CSV_PATH}")

DF = pd.read_csv(CSV_PATH)
DF = ensure_columns(DF)

COL_ID = pick_col(DF, ["show_id", "id", "movie_id", "ID"])
COL_TITLE = pick_col(DF, ["title", "Titre", "name", "Name"])
COL_YEAR = pick_col(DF, ["year", "Year", "annee", "Année"])

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
# Playwright scraping
# -----------------------------
async def scrape_search_motn(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Cherche un titre sur MovieOfTheNight via leur interface web (JS).
    IMPORTANT: adapte les sélecteurs ci-dessous à ce que ton scraper utilisait déjà.
    """
    q = query.strip()
    if not q:
        return []

    results: List[Dict[str, Any]] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # NOTE: /browse est une SPA JS. On l’utilise comme point d’entrée.
        await page.goto(f"{BASE_URL}/browse", wait_until="domcontentloaded")

        # ---- À ADAPTER : remplir la barre de recherche et lire les résultats ----
        # Exemple (fictif) :
        # await page.fill('input[placeholder="Search"]', q)
        # await page.wait_for_timeout(800)
        # items = await page.query_selector_all("a.show-card")
        # for it in items[:limit]:
        #    title = await it.inner_text()
        #    url = await it.get_attribute("href")

        # Fallback très générique : on essaie de trouver un input texte
        try:
            await page.wait_for_timeout(800)
            inputs = await page.query_selector_all("input")
            if inputs:
                # On prend le premier input visible
                await inputs[0].fill(q)
                await page.wait_for_timeout(1200)

            # On tente de récupérer des liens vers des pages de shows
            links = await page.query_selector_all('a[href*="/show/"], a[href*="/shows/"]')
            for a in links[:limit]:
                href = await a.get_attribute("href")
                text = (await a.inner_text()) or ""
                href = href or ""
                if "/show" in href or "/shows" in href:
                    full_url = href if href.startswith("http") else (BASE_URL + href)
                    title_guess = text.strip() if text.strip() else None
                    results.append({
                        "title": title_guess,
                        "motn_url": full_url,
                    })
        except PlaywrightTimeoutError:
            pass
        finally:
            await browser.close()

    # Dédup par URL
    seen = set()
    dedup = []
    for r in results:
        u = r.get("motn_url")
        if u and u not in seen:
            seen.add(u)
            dedup.append(r)
    return dedup[:limit]

async def scrape_rating_from_show_page(motn_url: str) -> Optional[float]:
    """
    Va sur la page du film/série et récupère la note actuelle.
    IMPORTANT: adapte le sélecteur de la note selon la page réelle.
    """
    if not motn_url:
        return None

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(motn_url, wait_until="domcontentloaded")

        # ---- À ADAPTER : sélecteurs rating ----
        # Souvent la note est visible comme un nombre type "8.3".
        # On tente une extraction générique.
        await page.wait_for_timeout(800)

        text = await page.inner_text("body")
        # Cherche un pattern "8.7" etc. (heuristique)
        candidates = re.findall(r"\b(\d\.\d)\b", text)
        if candidates:
            # Heuristique: prendre le plus grand (souvent la note principale est haute)
            vals = []
            for c in candidates:
                try:
                    vals.append(float(c))
                except:
                    pass
            if vals:
                await browser.close()
                return max(vals)

        await browser.close()
        return None

# -----------------------------
# MCP Tools (2 tools only)
# -----------------------------
@mcp.tool()
def search_movie(title: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Cache-first:
      1) search in CSV
      2) if empty -> scrape MovieOfTheNight, add minimal rows to CSV, return
    """
    global DF

    q = normalize_text(title)
    if not q:
        return []

    # 1) local search
    hits = DF[DF["_title_norm"].str.contains(re.escape(q), na=False)].copy()
    if not hits.empty:
        out = []
        for _, row in hits.head(max(1, int(limit))).iterrows():
            out.append({
                "id": safe_int(row[COL_ID]) if COL_ID else None,
                "title": safe_str(row[COL_TITLE]),
                "year": safe_int(row[COL_YEAR]) if COL_YEAR else None,
                "motn_url": safe_str(row["motn_url"]),
            })
        return out

    # 2) fallback scraping (sync wrapper around async)
    scraped = asyncio.run(scrape_search_motn(title, limit=limit))
    if not scraped:
        return []

    # Ajouter au CSV (minimum: title + motn_url; id si tu peux l’extraire)
    # Ici on crée des “pseudo-id” si tu n’as pas d’ID dans le CSV.
    if COL_ID is None:
        # crée un id interne
        if "internal_id" not in DF.columns:
            DF["internal_id"] = range(1, len(DF) + 1)
        COL_INTERNAL = "internal_id"
        next_id = int(DF[COL_INTERNAL].max()) + 1 if len(DF) else 1
    else:
        next_id = int(DF[COL_ID].max()) + 1 if len(DF) and DF[COL_ID].notna().any() else 1

    new_rows = []
    for r in scraped:
        new_title = r.get("title") or title
        new_url = r.get("motn_url")
        # avoid duplicates by url
        if new_url and (DF["motn_url"] == new_url).any():
            continue

        row = {c: None for c in DF.columns}
        row[COL_TITLE] = new_title
        row["_title_norm"] = normalize_text(new_title)
        row["motn_url"] = new_url
        row["rating_last_updated_at"] = None
        row["rating"] = None
        if COL_YEAR:
            row[COL_YEAR] = None

        if COL_ID:
            row[COL_ID] = next_id
        else:
            row["internal_id"] = next_id
        next_id += 1
        new_rows.append(row)

    if new_rows:
        DF = pd.concat([DF, pd.DataFrame(new_rows)], ignore_index=True)
        persist_df()

    # Refaire une recherche locale pour renvoyer proprement
    hits2 = DF[DF["_title_norm"].str.contains(re.escape(q), na=False)].copy()
    out = []
    for _, row in hits2.head(max(1, int(limit))).iterrows():
        out.append({
            "id": safe_int(row[COL_ID]) if COL_ID else safe_int(row.get("internal_id")),
            "title": safe_str(row[COL_TITLE]),
            "year": safe_int(row[COL_YEAR]) if COL_YEAR else None,
            "motn_url": safe_str(row["motn_url"]),
        })
    return out


@mcp.tool()
def get_movie(movie_id: int) -> Dict[str, Any]:
    """
    Retourne un film depuis le CSV.
    + refresh note si TTL dépassé (scrape page motn_url)
    + met à jour le CSV avec rating + rating_last_updated_at
    """
    global DF

    if movie_id is None:
        return {"found": False, "error": "movie_id is required"}

    # local lookup
    if COL_ID and COL_ID in DF.columns:
        rows = DF.loc[DF[COL_ID] == movie_id]
    elif "internal_id" in DF.columns:
        rows = DF.loc[DF["internal_id"] == movie_id]
    else:
        return {"found": False, "error": "No id column in CSV"}

    if rows.empty:
        return {"found": False, "movie_id": movie_id}

    idx = rows.index[0]
    row = DF.loc[idx]

    motn_url = safe_str(row.get("motn_url"))
    rating = safe_float(row.get("rating"))
    last_upd = row.get("rating_last_updated_at")

    # Parse last updated
    last_upd_ts: Optional[int] = None
    if last_upd is not None and not (isinstance(last_upd, float) and pd.isna(last_upd)):
        # accepte int unix ou ISO
        try:
            last_upd_ts = int(float(last_upd))
        except Exception:
            try:
                last_upd_ts = int(datetime.fromisoformat(str(last_upd)).timestamp())
            except Exception:
                last_upd_ts = None

    # refresh if stale or missing
    stale = (last_upd_ts is None) or (now_ts() - last_upd_ts > RATING_TTL_SECONDS)

    refreshed_rating = None
    if stale and motn_url:
        try:
            refreshed_rating = asyncio.run(scrape_rating_from_show_page(motn_url))
        except Exception:
            refreshed_rating = None

        if refreshed_rating is not None:
            DF.at[idx, "rating"] = float(refreshed_rating)
            DF.at[idx, "rating_last_updated_at"] = now_ts()
            persist_df()
            rating = float(refreshed_rating)

    return {
        "found": True,
        "id": safe_int(row[COL_ID]) if COL_ID else safe_int(row.get("internal_id")),
        "title": safe_str(row[COL_TITLE]),
        "year": safe_int(row[COL_YEAR]) if COL_YEAR else None,
        "motn_url": motn_url,
        "rating": rating,
        "rating_refreshed": refreshed_rating is not None,
        "rating_last_updated_at": DF.at[idx, "rating_last_updated_at"],
    }


if __name__ == "__main__":
    print(f"[OK] Loaded CSV: {CSV_PATH} | rows={len(DF)}")
    print(f"[OK] RATING_TTL_SECONDS={RATING_TTL_SECONDS}")
    mcp.run()
