from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.llm_service import llm_service

router = APIRouter(prefix="/chat", tags=["AI"])

class ChatRequest(BaseModel):
    prompt: str

@router.post("/")
async def ask_hephaestus(request: ChatRequest):
    # Appel au service Ollama
    response = await llm_service.generate_response(request.prompt)
    if "Erreur critique" in response:
        raise HTTPException(status_code=500, detail=response)
    return {"response": response}
