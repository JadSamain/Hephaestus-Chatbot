from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Hephaestus Backend", version="0.1.0")

# Configuration CORS (Critique pour que le Frontend puisse appeler le Backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En prod, restreindre à l'URL du frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Vérifie si l'API est en ligne."""
    return {"status": "ok", "service": "hephaestus-backend"}

if __name__ == "__main__":
    import uvicorn
    # Reload=True permet le redémarrage auto quand tu modifies le code
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)