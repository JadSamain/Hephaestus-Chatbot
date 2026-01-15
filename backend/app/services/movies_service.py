import pandas as pd
import os
from typing import List, Dict, Optional

class MoviesService:
    def __init__(self, csv_path: str = None):
        if csv_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            backend_dir = os.path.dirname(os.path.dirname(current_dir))
            csv_path = os.path.join(backend_dir, "data", "movies_catalog.csv")
        
        self.csv_path = csv_path
        self.df = None
        self._last_modified_time = 0
        self._load_data()
    
    def _is_file_modified(self) -> bool:
        try:
            if not os.path.exists(self.csv_path):
                return False
            current_mtime = os.path.getmtime(self.csv_path)
            return current_mtime > self._last_modified_time
        except Exception:
            return False

    def _load_data(self):
        try:
            if os.path.exists(self.csv_path):
                self._last_modified_time = os.path.getmtime(self.csv_path)
                self.df = pd.read_csv(self.csv_path, sep=';', decimal=',')
            else:
                self.df = pd.DataFrame()
        except Exception:
            self.df = pd.DataFrame()
    
    def get_all_movies(self) -> List[Dict]:
        if self._is_file_modified():
            self._load_data()
            
        if self.df is None or self.df.empty:
            return []
        
        movies = []
        for _, row in self.df.iterrows():
            try:
                platforms_raw = row.get("platforms", "")
                platforms_list = self._parse_platforms(platforms_raw)
                
                movie = {
                    "id": int(row.get("show_id", 0)) if pd.notna(row.get("show_id")) else 0,
                    "title": str(row.get("title", "Unknown")),
                    "year": int(row.get("year", 0)) if pd.notna(row.get("year")) else None,
                    "rating": float(row.get("rating", 0)) if pd.notna(row.get("rating")) else 0,
                    "poster": str(row.get("poster_url", "")),
                    "platforms": platforms_list,
                    "genre": str(row.get("tags", "")) if pd.notna(row.get("tags")) else "",
                    "synopsis": str(row.get("summary", "")) if pd.notna(row.get("summary")) else "Synopsis non disponible",
                    "director": str(row.get("director", "")) if pd.notna(row.get("director")) else "Inconnu",
                    "actors": [a.strip() for a in str(row.get("starring", "")).split(",")[:3]] if pd.notna(row.get("starring")) else []
                }
                movies.append(movie)
            except Exception:
                continue
        
        return movies
    
    def filter_by_platform(self, platform: str) -> List[Dict]:
        all_movies = self.get_all_movies()
        
        if platform.lower() == "all":
            return all_movies
        
        filtered = [
            movie for movie in all_movies 
            if platform in movie.get("platforms", [])
        ]
        
        return filtered
    
    def group_by_category(self, platform: Optional[str] = None) -> Dict[str, List[Dict]]:
        movies = self.filter_by_platform(platform) if platform else self.get_all_movies()
        
        categories = {}
        for movie in movies:
            genre_raw = movie.get("genre", "Autres")
            if not genre_raw or genre_raw == "":
                genre_raw = "Autres"
            
            primary_genre = genre_raw.split(",")[0].strip()
            
            if primary_genre not in categories:
                categories[primary_genre] = []
            
            categories[primary_genre].append(movie)
        
        result = []
        for category_name, category_movies in categories.items():
            result.append({
                "title": category_name,
                "movies": category_movies
            })
        
        return result
    
    def get_available_platforms(self) -> List[str]:
        all_movies = self.get_all_movies()
        platforms = set()
        
        for movie in all_movies:
            platforms.update(movie.get("platforms", []))
        
        return sorted(list(platforms))
    
    def _parse_platforms(self, platforms_str) -> List[str]:
        if pd.isna(platforms_str) or platforms_str == "":
            return []
        
        if isinstance(platforms_str, list):
            return platforms_str
        
        platforms_str = str(platforms_str)
        if "," in platforms_str:
            return [p.strip() for p in platforms_str.split(",")]
        elif ";" in platforms_str:
            return [p.strip() for p in platforms_str.split(";")]
        else:
            return [platforms_str.strip()]

movies_service = MoviesService()
