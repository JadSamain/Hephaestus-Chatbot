import json
import re
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

# Import du service LLM
from app.services.llm_service import llm_service

router = APIRouter(prefix="/chat", tags=["AI"])

# --- MODÈLES DE DONNÉES ---
class ChatRequest(BaseModel):
    prompt: str

class ToolCall(BaseModel):
    """Structure validée par Pydantic pour l'appel d'outil"""
    action: str
    parameters: Dict[str, Any]

# --- OUTIL PLACEHOLDER (Simulation) ---
async def get_movie_data_placeholder(title: str):
    """Simule le futur outil de scrapping (Jour 4)"""
    print(f"    [TOOL] Exécution de get_movie_data pour: {title}")
    return {
        "title": title,
        "rating": "8.5/10 (IMDb)",
        "streaming": ["Netflix", "Disney+"],
        "status": "Success"
    }

# --- LOGIQUE DU ROUTEUR ---
@router.post("/")
async def ask_hephaestus(request: ChatRequest):
    user_prompt = request.prompt
    
    # 1. Premier passage : Le LLM décide s'il a besoin d'un outil [cite: 33, 119]
    raw_response = await llm_service.generate_response(user_prompt)
    
    # Extraction du JSON (ignore le texte inutile autour)
    json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)

    if json_match:
        try:
            clean_json = json_match.group()
            print(f"[*] JSON EXTRACTED : {clean_json}") 
            data = json.loads(clean_json)
            tool_request = ToolCall(**data)

            if tool_request.action == "get_movie_data":
                movie_title = tool_request.parameters.get("title", "Inconnu")
                
                # 2. Exécution de l'action externe (Tooling) [cite: 111, 264]
                tool_result = await get_movie_data_placeholder(movie_title)
                
                # 3. Second passage : Synthèse des données en langage naturel [cite: 119, 214]
                # On ne renvoie PAS tool_result au front, on le renvoie au LLM
                synthesis_prompt = (
                    f"Tu es un expert cinéma. L'utilisateur demande : '{user_prompt}'. "
                    f"Voici les données réelles trouvées : {tool_result}. "
                    "Réponds à l'utilisateur de manière naturelle sans mentionner de JSON."
                )
                
                final_answer = await llm_service.generate_response(synthesis_prompt)
                return {"response": final_answer}

        except Exception as e:
            print(f"[!] Erreur de boucle : {e}")

    # Réponse par défaut si aucun outil n'est requis ou si le parsing échoue
    return {"response": raw_response}