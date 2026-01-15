from __future__ import annotations

import os
import re
import csv
import time
import asyncio
from typing import Any, Dict, List, Optional

import pandas as pd
from mcp.server.fastmcp import FastMCP
from playwright.async_api import async_playwright

# -----------------------------
# CONFIGURATION
# -----------------------------
mcp = FastMCP("hephaestus-mega-scraper")

# Chemins
CSV_PATH = os.getenv("MOVIES_CSV_PATH", "data/movies_catalog.csv")
BASE_URL_MOTN = "https://www.movieofthenight.com"

# Colonnes garanties dans le CSV
REQUIRED_COLUMNS = [
    "show_id", "title", "year", "motn_url", 
    "rating", "rating_last_updated_at", "_title_norm"
]

# -----------------------------
# 1. GESTION BASE DE DONNÉES (ROBUSTE)
# -----------------------------
def normalize_text(s: Any) -> str:
    s = "" if pd.isna(s) or s is None else str(s)
    return re.sub(r"\s+", " ", s.strip().lower())

def atomic_write_csv(df: pd.DataFrame, path: str) -> None:
    """Sauvegarde sécurisée avec point-virgule pour compatibilité Excel FR."""
    tmp = path + ".tmp"
    # QUOTE_ALL pour gérer les titres bizarres, sep=";" pour Excel
    df.to_csv(tmp, index=False, sep=";", quoting=csv.QUOTE_ALL, encoding='utf-8')
    os.replace(tmp, path)
    print(f"[CSV] Sauvegarde : {len(df)} films.")

def load_or_init_csv() -> pd.DataFrame:
    if not os.path.exists(CSV_PATH):
        return pd.DataFrame(columns=REQUIRED_COLUMNS)
    try:
        # 1. Lecture permissive
        df = pd.read_csv(CSV_PATH, sep=None, engine='python', on_bad_lines='skip', encoding='utf-8')
        
        # 2. [CORRECTION] Migration de schéma : Ajout des colonnes manquantes
        for col in REQUIRED_COLUMNS:
            if col not in df.columns:
                print(f"[CSV] Colonne manquante détectée : {col}. Ajout automatique.")
                df[col] = None # ou "" selon préférence

        # 3. Nettoyage de la colonne rating
        if "rating" in df.columns:
            # Conversion en string pour manipuler, puis replace, puis numeric
            df["rating"] = df["rating"].astype(str).str.replace(',', '.', regex=False)
            df["rating"] = pd.to_numeric(df["rating"], errors='coerce')
            
        return df
    except Exception as e:
        print(f"[ERR] Erreur chargement CSV: {e}")
        # En cas de fichier corrompu, on repart sur une base propre pour éviter le crash en boucle
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

# Chargement initial
DF = load_or_init_csv()
# Réparation des types
if "show_id" in DF.columns:
    DF["show_id"] = pd.to_numeric(DF["show_id"], errors='coerce').fillna(0).astype(int)
DF["title"] = DF["title"].fillna("").astype(str)
DF["_title_norm"] = DF["title"].apply(normalize_text)
print(f"✓ Système prêt : {len(DF)} films en mémoire.")

# -----------------------------
# 2. MOTEUR DE SCRAPING (PLAYWRIGHT)
# -----------------------------
async def get_browser_context(p):
    """Configuration navigateur furtif pour éviter les blocages."""
    browser = await p.chromium.launch(headless=True)
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        locale="fr-FR"
    )
    return browser, context

async def scrape_metadata_motn(query: str, limit: int = 5) -> List[Dict]:
    """Scrape les infos générales (Année, Note, Streaming) sur MovieOfTheNight."""
    results = []
    print(f"[Scraper META] Recherche : {query}")
    
    async with async_playwright() as p:
        browser, context = await get_browser_context(p)
        try:
            page = await context.new_page()
            # Navigation robuste (60s timeout)
            try:
                await page.goto(f"{BASE_URL_MOTN}/browse", wait_until="domcontentloaded", timeout=60000)
            except:
                print("[Scraper META] Timeout accès site.")
                return []

            await page.wait_for_timeout(2000)

            # Saisie recherche
            inputs = await page.locator("input[type='text']").all()
            if not inputs: inputs = await page.locator("input").all()
            
            if inputs:
                await inputs[0].fill(query)
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(4000) # Attente résultats

                # Extraction
                links = await page.locator("a[href*='/show/']").all()
                for link in links:
                    href = await link.get_attribute("href")
                    text = await link.inner_text() or ""
                    
                    # Nettoyage et Parsing
                    lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 1]
                    title = next((l for l in lines if not re.match(r'^[\d\.,]+$', l)), None)
                    
                    if title and href:
                        # Regex Année/Note
                        year = re.search(r'\b(19|20)\d{2}\b', text)
                        rating = re.search(r'\b(\d\.\d)\b', text)
                        
                        results.append({
                            "title": title,
                            "year": int(year.group(0)) if year else None,
                            "rating": float(rating.group(1)) if rating else None,
                            "motn_url": href if href.startswith("http") else BASE_URL_MOTN + href
                        })
                        if len(results) >= limit: break
        except Exception as e:
            print(f"[Scraper META CRASH] {e}")
        finally:
            await browser.close()
            
    # Déduplication
    seen = set()
    unique = []
    for r in results:
        if r["motn_url"] not in seen:
            seen.add(r["motn_url"])
            unique.append(r)
    return unique

async def scrape_cinefil_showtimes(movie: str, city: str) -> Dict[str, Any]:
    """
    NOUVEAU : Cherche les séances pour un film et une ville.
    Stratégie : Google Search 'site:cinefil.com' -> Page directe -> Scraping.
    """
    print(f"[Scraper SEANCES] Recherche : {movie} à {city}")
    data = {"movie": movie, "city": city, "theaters": [], "url": None}
    
    async with async_playwright() as p:
        browser, context = await get_browser_context(p)
        try:
            page = await context.new_page()
            
            # 1. Trouver la page Cinefil via Google (plus fiable que le moteur interne Cinefil)
            search_q = f"site:cinefil.com seance film {movie} {city}"
            google_url = f"https://www.google.com/search?q={search_q.replace(' ', '+')}"
            
            await page.goto(google_url, wait_until="domcontentloaded", timeout=30000)
            
            # Accepter cookies Google si besoin (rapide)
            try:
                await page.locator("button:has-text('Tout refuser')").click(timeout=2000)
            except: pass

            # Prendre le 1er résultat pertinent
            # On cherche un lien qui contient 'cinefil.com'
            result_link = page.locator("a[href*='cinefil.com']").first
            
            if await result_link.count() > 0:
                target_url = await result_link.get_attribute("href")
                data["url"] = target_url
                print(f"[Scraper SEANCES] Cible trouvée : {target_url}")
                
                # 2. Scraper la page Cinefil
                await page.goto(target_url, wait_until="domcontentloaded", timeout=45000)
                
                # Gestion cookies Cinefil (Important !)
                try:
                    await page.locator(".cmp-cta-reject").click(timeout=3000)
                except: pass

                # Extraction des cinémas et horaires
                # Sélecteur typique Cinefil: .cinema-line ou structure similaire
                # Note: La structure peut varier, on fait du 'best effort'
                
                # On cherche les blocs de cinémas
                cinemas = await page.locator(".bloc-seance").all() # Sélecteur hypothétique générique
                if not cinemas:
                    cinemas = await page.locator("div[itemtype='http://schema.org/MovieTheater']").all()

                count = 0
                for cine in cinemas:
                    if count > 5: break # Max 5 cinémas
                    name_el = cine.locator("h3, h2, .name, .cinema-title").first
                    name = await name_el.inner_text() if await name_el.count() > 0 else "Cinéma Inconnu"
                    
                    # Horaires (souvent dans des span ou div avec classe hours)
                    times_el = await cine.locator(".seance-heure, .t-heure, time").all()
                    times = [await t.inner_text() for t in times_el]
                    # Nettoyage des horaires vides
                    times = [t.strip() for t in times if len(t.strip()) > 2]
                    
                    if times:
                        data["theaters"].append({
                            "name": name.strip(),
                            "showtimes": times[:8] # Limite horaires
                        })
                        count += 1
            else:
                print("[Scraper SEANCES] Pas de lien Cinefil trouvé sur Google.")

        except Exception as e:
            print(f"[Scraper SEANCES ERR] {e}")
        finally:
            await browser.close()
            
    return data

# -----------------------------
# 3. OUTILS MCP EXPOSÉS
# -----------------------------

@mcp.tool()
async def search_movie(title: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Outil PRINCIPAL pour identifier un film.
    Cherche le film, remplit la base de données metadata, et renvoie les infos de base.
    """
    global DF
    q_norm = normalize_text(title)
    
    # 1. Cache Local
    mask = DF["_title_norm"].astype(str).str.contains(re.escape(q_norm), case=False, na=False)
    hits = DF[mask].replace({float("nan"): None}).to_dict(orient="records")
    
    if hits:
        # Tri : titre le plus court d'abord (match exact)
        hits.sort(key=lambda x: len(str(x["title"])))
        print(f"[Cache] Trouvé : {hits[0]['title']}")
        return hits[:limit]

    # 2. Scraping Metadata
    # On passe bien la limite au scraper
    scraped = await scrape_metadata_motn(title, limit=limit)
    if not scraped:
        return []

    # Tri pertinence
    scraped.sort(key=lambda x: len(x["title"]))

    # 3. Sauvegarde CSV
    new_rows = []
    # Calcul ID robuste
    max_id = 0
    if not DF.empty and "show_id" in DF.columns:
        try:
            max_id = int(DF["show_id"].max())
        except:
            pass
    next_id = max_id + 1
    
    ts = int(time.time())

    for item in scraped:
        if not DF[DF["motn_url"] == item["motn_url"]].empty: continue
        
        row = {
            "show_id": next_id,
            "title": item["title"],
            "year": item["year"],
            "motn_url": item["motn_url"],
            "rating": item["rating"],
            "rating_last_updated_at": ts if item["rating"] else None,
            "_title_norm": normalize_text(item["title"])
        }
        new_rows.append(row)
        next_id += 1
    
    if new_rows:
        new_df = pd.DataFrame(new_rows)
        DF = pd.concat([DF, new_df], ignore_index=True)
        atomic_write_csv(DF, CSV_PATH)
        # On renvoie les N premiers résultats
        return new_df.head(limit).replace({float("nan"): None}).to_dict(orient="records")
    
    return []

@mcp.tool()
async def get_showtimes(movie_title: str, city: str) -> Dict[str, Any]:
    """
    Outil SÉANCES : Trouve où et quand voir un film dans une ville donnée.
    Utilise une recherche Web live (Cinefil via Google).
    Retourne la liste des cinémas et horaires.
    """
    # On valide le film d'abord si besoin, mais ici on lance direct la recherche large
    results = await scrape_cinefil_showtimes(movie_title, city)
    
    if not results["theaters"]:
        return {
            "found": False, 
            "message": f"Aucune séance trouvée pour '{movie_title}' à {city}. Vérifiez que le film est encore à l'affiche.",
            "source_url": results.get("url")
        }
    
    return {
        "found": True,
        "movie": results["movie"],
        "city": results["city"],
        "theaters": results["theaters"],
        "source": "Cinefil via Hephaestus Scraper",
        "link": results["url"]
    }

@mcp.tool()
async def get_movie(show_id: int) -> Dict[str, Any]:
    """
    Récupère les détails d'un film via son ID.
    Nommé 'get_movie' pour compatibilité stricte avec chat.py.
    """
    global DF
    
    try:
        clean_id = int(show_id)
    except (ValueError, TypeError):
        return {"found": False, "error": "ID invalide"}

    # Filtrage DataFrame
    row = DF[DF["show_id"] == clean_id]
    if row.empty:
        return {"found": False, "error": "ID introuvable en cache"}
    
    r = row.iloc[0]
    return {
        "found": True,
        "title": r["title"],
        "year": int(r["year"]) if pd.notna(r["year"]) else None,
        "rating": float(r["rating"]) if pd.notna(r["rating"]) else None,
        "url": r["motn_url"]
    }