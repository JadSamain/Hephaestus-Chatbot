from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import chat

app = FastAPI(title="Hephaestus Backend", version="0.1.0")

# Configuration CORS (Indispensable pour la communication avec React sur le port 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion du router de chat (défini dans app/routers/chat.py)
app.include_router(chat.router)

@app.get("/health")
async def health_check():
    """Vérifie si l'API est en ligne."""
    return {"status": "ok", "service": "hephaestus-backend"}

if __name__ == "__main__":
    import uvicorn
    # Le paramètre reload=True permet de redémarrer le serveur à chaque modification
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)