from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.services.movies_service import movies_service

router = APIRouter(prefix="/films", tags=["films"])

@router.get("/")
async def get_films(platform: Optional[str] = Query(None, description="Filter by platform")):
    """
    Get all films grouped by category.
    Optionally filter by streaming platform.
    """
    try:
        categories = movies_service.group_by_category(platform)
        return {
            "success": True,
            "categories": categories,
            "total": sum(len(cat["movies"]) for cat in categories)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving films: {str(e)}")

@router.get("/platforms")
async def get_platforms():
    """Get list of all available streaming platforms."""
    try:
        platforms = movies_service.get_available_platforms()
        return {
            "success": True,
            "platforms": platforms
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving platforms: {str(e)}")

@router.get("/all")
async def get_all_films():
    """Get all films without grouping."""
    try:
        movies = movies_service.get_all_movies()
        return {
            "success": True,
            "movies": movies,
            "total": len(movies)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving films: {str(e)}")
