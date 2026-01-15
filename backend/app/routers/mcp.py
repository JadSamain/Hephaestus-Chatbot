import os
import re
import asyncio
import pandas as pd
from typing import Optional, Dict, Any
from mcp.server.fastmcp import FastMCP
from playwright.async_api import async_playwright

# --- CONFIGURATION ---
mcp = FastMCP("movie-smart-search")
CSV_PATH = "data/movies_catalog.csv" # Vérifie que ce chemin est bon par rapport à ton lancement
BASE_URL = "https://www.movieofthenight.com"

# --- CHARGEMENT DU CSV ---
def load_csv():
    if os.path.exists(CSV_PATH):
        # Important: le séparateur est le point-virgule selon ton fichier
        return pd.read_csv(CSV_PATH, sep=";")
    return pd.DataFrame(columns=[
        "show_id", "show_url", "title", "poster_url", "rating", 
        "year", "tags", "duration_minutes", "summary", 
        "director", "starring", "platforms"
    ])

# Variable globale pour éviter de recharger le disque à chaque fois
DF = load_csv()

def save_csv():
    global DF
    # Sauvegarde atomique simple
    DF.to_csv(CSV_PATH, sep=";", index=False, quoting=1) # quote_all pour sécurité

def normalize(text):
    return str(text).lower().strip() if text else ""

# --- LE CŒUR DU SYSTÈME ---

@mcp.tool()
async def find_movie_smart(title: str) -> Dict[str, Any]:
    """
    Cherche un film par titre. 
    1. Regarde dans le CSV local.
    2. Si absent : Scrape le web, ajoute au CSV, et renvoie les infos.
    """
    global DF
    print(f"[SMART SEARCH] Recherche : {title}")
    
    # 1. RECHERCHE LOCALE
    # On cherche si le titre existe (case insensitive)
    mask = DF['title'].apply(normalize).str.contains(normalize(title), na=False)
    results = DF[mask]
    
    if not results.empty:
        print(f"[CACHE HIT] Trouvé dans CSV : {results.iloc[0]['title']}")
        # Convertit la ligne en dictionnaire propre (remplace NaN par None)
        return results.iloc[0].where(pd.notnull(results.iloc[0]), None).to_dict()

    # 2. SCRAPING (Si pas trouvé)
    print("[CACHE MISS] Lancement du scraping Playwright...")
    scraped_data = await scrape_movie_data(title)
    
    if scraped_data:
        # Ajout au DataFrame
        new_row = pd.DataFrame([scraped_data])
        DF = pd.concat([DF, new_row], ignore_index=True)
        
        # Sauvegarde immédiate
        save_csv()
        print(f"[SAVE] Film sauvegardé dans {CSV_PATH}")
        return scraped_data
    
    return {"error": "Film introuvable sur le web."}

async def scrape_movie_data(query: str) -> Optional[Dict[str, Any]]:
    """Logique de scraping Playwright"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Recherche sur le site (exemple générique adapté à MovieOfTheNight si possible, ou Google)
        # Ici on simule une recherche directe pour l'exemple. 
        # Si le site a une barre de recherche, il faut l'utiliser.
        # Pour l'exemple robuste, on va tenter d'aller sur une URL de recherche fictive ou Google :
        
        try:
            # Astuce: On cherche via Google pour trouver l'URL directe du site
            search_url = f"https://www.google.com/search?q=site:movieofthenight.com {query}"
            await page.goto(search_url)
            
            # On prend le premier lien qui matche le site
            link_locator = page.locator("a[href*='movieofthenight.com/show/']").first
            if await link_locator.count() > 0:
                url = await link_locator.get_attribute("href")
                print(f"[SCRAPE] URL trouvée : {url}")
                await page.goto(url)
                
                # Extraction des données (sélecteurs À ADAPTER selon le site réel)
                # Ceci est une structure hypothétique basée sur ton CSV
                data = {
                    "show_id": int(re.search(r'show/(\d+)', url).group(1)) if re.search(r'show/(\d+)', url) else 0,
                    "show_url": url,
                    "title": await page.title(), # Ou un sélecteur h1 spécifique
                    "year": "2024", # À extraire
                    "rating": "0.0", # À extraire
                    "summary": "Scraped summary", # À extraire
                    "platforms": "Netflix" # À extraire
                }
                # Pour la démo, on remplit le reste avec des vides pour matcher le CSV
                for col in DF.columns:
                    if col not in data:
                        data[col] = None
                
                return data
            else:
                print("[SCRAPE] Pas de lien pertinent trouvé.")
                return None
                
        except Exception as e:
            print(f"[SCRAPE ERROR] {e}")
            return None
        finally:
            await browser.close()