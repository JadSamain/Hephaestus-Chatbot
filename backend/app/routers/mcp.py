from __future__ import annotations

import os
import re
import csv
import time
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

import pandas as pd
from mcp.server.fastmcp import FastMCP
from playwright.async_api import async_playwright

# -----------------------------
# Config
# -----------------------------
mcp = FastMCP("hephaestus-movies-cache-refresh")

# Chemin absolu ou relatif
CSV_PATH = os.getenv("MOVIES_CSV_PATH", "data/movies_catalog.csv")
RATING_TTL_SECONDS = int(os.getenv("RATING_TTL_SECONDS", str(24 * 3600)))  # 24h
BASE_URL = "https://www.movieofthenight.com"

# Colonnes obligatoires
REQUIRED_COLUMNS = ["show_id", "title", "year", "motn_url", "rating", "rating_last_updated_at"]

# -----------------------------
# Utils & CSV Safety
# -----------------------------
def normalize_text(s: Any) -> str:
    s = "" if pd.isna(s) or s is None else str(s)
    s = s.strip().lower()
    return re.sub(r"\s+", " ", s)

def atomic_write_csv(df: pd.DataFrame, path: str) -> None:
    """Écriture sécurisée avec guillemets forcés partout (QUOTE_ALL)."""
    tmp = path + ".tmp"
    # QUOTE_ALL protège contre les virgules dans les titres
    df.to_csv(tmp, index=False, quoting=csv.QUOTE_ALL, encoding='utf-8')
    os.replace(tmp, path)
    print(f"[CSV] Sauvegarde effectuée : {len(df)} films en base.")

def load_or_init_csv() -> pd.DataFrame:
    if not os.path.exists(CSV_PATH):
        print(f"[WARN] CSV introuvable. Création : {CSV_PATH}")
        return pd.DataFrame(columns=REQUIRED_COLUMNS)
    try:
        df = pd.read_csv(CSV_PATH, on_bad_lines='skip', encoding='utf-8')
        # Vérif des colonnes
        for col in REQUIRED_COLUMNS:
            if col not in df.columns:
                df[col] = None
        return df
    except Exception as e:
        print(f"[ERR] CSV Corrompu ({e}). Reset.")
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

# Initialisation du Cache
DF = load_or_init_csv()
if "_title_norm" not in DF.columns:
    DF["_title_norm"] = DF["title"].astype(str).apply(normalize_text)

# -----------------------------
# Scraper Logic (ROBUSTE)
# -----------------------------

async def scrape_search_motn(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    results = []
    print(f"[Scraper] Démarrage Playwright pour : {query}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        
        try:
            page = await context.new_page()
            # 1. Navigation
            await page.goto(f"{BASE_URL}/browse", wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(2000)

            # 2. Recherche
            inputs = await page.locator("input[type='text']").all()
            search_input = inputs[0] if inputs else page.locator("input").first

            if search_input:
                await search_input.fill(query)
                await page.keyboard.press("Enter")
                print("[Scraper] Recherche envoyée...")
                await page.wait_for_timeout(4000) # Attente résultats

                # 3. Extraction Intelligente
                # On récupère tous les liens qui semblent être des fiches films
                links = await page.locator("a[href*='/show/']").all()
                
                for link in links:
                    href = await link.get_attribute("href")
                    # On prend tout le texte contenu dans le lien (Titre + Année + Note souvent groupés)
                    raw_text = await link.inner_text() 
                    
                    if not href or not raw_text:
                        continue

                    # --- FILTRAGE ET NETTOYAGE ---
                    
                    # 1. Nettoyage du titre : on prend la ligne la plus longue qui n'est pas un nombre
                    lines = [l.strip() for l in raw_text.split('\n') if l.strip()]
                    title_candidate = None
                    
                    # On cherche une ligne qui ressemble à un titre (pas juste des chiffres)
                    for line in lines:
                        # Si la ligne n'est pas juste un nombre (ex: "6.1" ou "2024")
                        if not re.match(r'^[\d\.,\s%]+$', line): 
                            title_candidate = line
                            break
                    
                    # Si on n'a rien trouvé ou que le titre est trop court, on zappe (c'est sûrement un badge)
                    if not title_candidate or len(title_candidate) < 2:
                        continue

                    # 2. Extraction Année (Regex cherche 4 chiffres: 19xx ou 20xx)
                    year = None
                    year_match = re.search(r'\b(19|20)\d{2}\b', raw_text)
                    if year_match:
                        year = int(year_match.group(0))

                    # 3. Extraction Note (Regex cherche un float: 8.8)
                    rating = None
                    rating_match = re.search(r'\b(\d\.\d)\b', raw_text)
                    if rating_match:
                        rating = float(rating_match.group(1))

                    full_url = href if href.startswith("http") else BASE_URL + href
                    
                    results.append({
                        "title": title_candidate,
                        "year": year,           # Rempli maintenant
                        "rating": rating,       # Rempli maintenant
                        "motn_url": full_url
                    })
                    
                    if len(results) >= limit:
                        break
            else:
                print("[Scraper ERR] Input introuvable.")

        except Exception as e:
            print(f"[Scraper CRASH] {e}")
        finally:
            await browser.close()
    
    # Déduplication
    seen = set()
    unique = []
    for r in results:
        if r["motn_url"] not in seen:
            seen.add(r["motn_url"])
            unique.append(r)
            
    print(f"[Scraper] Trouvé {len(unique)} résultats complets.")
    return unique
    
    # Déduplication
    seen = set()
    unique = []
    for r in results:
        if r["motn_url"] not in seen:
            seen.add(r["motn_url"])
            unique.append(r)
            
    print(f"[Scraper] Trouvé {len(unique)} résultats.")
    return unique

async def scrape_rating_from_show_page(motn_url: str) -> Optional[float]:
    # (Garde ta logique existante ou simplifiée ici, ce n'est pas le bloquant actuel)
    return None 

# -----------------------------
# MCP Tools (Exposed)
# -----------------------------

@mcp.tool()
async def search_movie(title: str, limit: int = 5) -> List[Dict[str, Any]]:
    global DF
    q_norm = normalize_text(title)
    
    # 1. Recherche Locale (Cache Hit)
    mask = DF["_title_norm"].astype(str).str.contains(re.escape(q_norm), case=False, na=False)
    hits = DF[mask]
    
    # Tri des hits locaux aussi (Exact match en premier)
    if not hits.empty:
        # On convertit en liste de dicts pour trier
        hits_list = hits.replace({float("nan"): None}).to_dict(orient="records")
        # Tri: Ceux qui matchent exactement la longueur du titre recherché passent en premier
        hits_list.sort(key=lambda x: len(str(x["title"])))
        
        print(f"[Cache] Film trouvé en local : {hits_list[0]['title']}")
        return hits_list[:limit]

    # 2. Scraping (Cache Miss)
    print(f"[Cache] Film absent. Lancement Scraper pour : {title}")
    scraped_data = await scrape_search_motn(title, limit=limit)
    
    if not scraped_data:
        print("[Cache] Scraper n'a rien trouvé.")
        return []

    # --- CORRECTION MAJEURE : TRI PAR PERTINENCE ---
    # On trie pour que le titre le plus court (souvent le film original) soit premier.
    # Ex: "Inception" (9 chars) passera devant "Inception: The Cobol Job" (24 chars)
    scraped_data.sort(key=lambda x: len(x["title"]))
    
    # Optionnel: Tu peux aussi forcer l'exact match en priorité absolue
    scraped_data.sort(key=lambda x: 0 if normalize_text(x["title"]) == q_norm else 1)

    # 3. ÉCRITURE DANS LE CSV
    new_rows = []
    
    # Gestion ID
    max_id = 0
    if not DF.empty and "show_id" in DF.columns:
        try:
            max_id = int(DF["show_id"].max())
        except:
            pass
    next_id = max_id + 1
    
    current_ts = int(time.time())

    for item in scraped_data:
        # Eviter doublons URL
        if not DF[DF["motn_url"] == item["motn_url"]].empty:
            continue
            
        new_row = {
            "show_id": next_id,
            "title": item["title"],
            "year": item.get("year"),
            "motn_url": item["motn_url"],
            "rating": item.get("rating"),
            "rating_last_updated_at": current_ts if item.get("rating") else None,
            "_title_norm": normalize_text(item["title"])
        }
        new_rows.append(new_row)
        next_id += 1
    
    if new_rows:
        new_df = pd.DataFrame(new_rows)
        DF = pd.concat([DF, new_df], ignore_index=True)
        atomic_write_csv(DF, CSV_PATH)
        print(f"[MCP] {len(new_rows)} nouveaux films ajoutés et triés.")
        
        # Retour propre pour le chat
        return new_df.replace({float("nan"): None}).to_dict(orient="records")
        
    return []

@mcp.tool()
async def get_movie(movie_id: Any) -> Dict[str, Any]:
    # Ta fonction get_movie existante...
    # Assure-toi juste qu'elle cast l'ID : int(movie_id)
    global DF
    try:
        clean_id = int(movie_id)
    except:
        return {"found": False, "error": "ID invalide"}
        
    row = DF[DF["show_id"] == clean_id]
    if row.empty:
        return {"found": False}
    
    r = row.iloc[0]
    return {
        "found": True,
        "title": r["title"],
        "url": r["motn_url"],
        "rating": r["rating"]
    }