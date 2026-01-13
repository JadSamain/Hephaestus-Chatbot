import json
import re
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any

# Import du service modifié
from app.services.llm_service import llm_service

router = APIRouter(prefix="/chat", tags=["AI"])

class ChatRequest(BaseModel):
    prompt: str

class ToolCall(BaseModel):
    action: str
    parameters: Dict[str, Any]

# --- OUTIL PLACEHOLDER ---
async def get_movie_data_placeholder(title: str):
    # Simulation de données propres
    return {
        "title": title,
        "director": "James Cameron",
        "year": 2009,
        "rating": "7.9/10 (IMDb)",
        "plot": "Un marine paraplégique est envoyé sur la lune Pandora...",
        "streaming": ["Disney+", "Canal+"]
    }

# --- ROUTE PRINCIPALE ---
@router.post("/")
async def ask_hephaestus(request: ChatRequest):
    user_prompt = request.prompt
    
    # ÉTAPE 1 : ROUTING (Utilise le ROUTER_SYSTEM_PROMPT par défaut)
    print(f"[*] 1. Routing de : {user_prompt}")
    raw_response = await llm_service.generate_response(user_prompt)
    print(f"[*] Réponse Routeur : {raw_response}")

    # ÉTAPE 2 : DÉTECTION
    json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)

    if json_match:
        try:
            json_str = json_match.group()
            data = json.loads(json_str)
            tool_request = ToolCall(**data)

            if tool_request.action == "get_movie_data":
                # Exécution de l'outil
                movie_title = tool_request.parameters.get("title")
                tool_result = await get_movie_data_placeholder(movie_title)
                
                # ÉTAPE 3 : SYNTHÈSE (AVEC UN NOUVEAU SYSTEM PROMPT)
                # On force le LLM à changer de rôle : il n'est plus routeur, il est présentateur.
                
                writer_system_prompt = """
                Tu es un assistant cinéma expert et enthousiaste.
                Ton rôle est de présenter les informations fournies par l'outil de manière naturelle.
                Ne mentionne pas "le JSON" ou "l'outil". Parle directement à l'utilisateur.
                """
                
                final_user_prompt = (
                    f"L'utilisateur a demandé : '{user_prompt}'. "
                    f"Voici les données officielles récupérées : {json.dumps(tool_result, ensure_ascii=False)}. "
                    "Fais une réponse courte, précise et donne les plateformes de streaming."
                )
                
                # On passe le writer_system_prompt ici pour écraser le routeur
                final_answer = await llm_service.generate_response(
                    user_prompt=final_user_prompt, 
                    system_instruction=writer_system_prompt
                )
                
                return {"response": final_answer}

        except Exception as e:
            print(f"[!] Erreur : {e}")
            return {"response": "Désolé, j'ai eu un problème technique en cherchant le film."}

    # CAS B : Conversation simple (Le routeur a répondu en texte)
    return {"response": raw_response}