import json
import re
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

# Importe ton service LLM existant
from app.services.llm_service import llm_service
# IMPORT CRITIQUE : Le module de Mehdi
import app.mcp as mcp_tools 

router = APIRouter(prefix="/chat", tags=["AI"])

class ChatRequest(BaseModel):
    prompt: str

class ToolCall(BaseModel):
    action: str
    parameters: Dict[str, Any]

@router.post("/")
async def ask_hephaestus(request: ChatRequest):
    user_prompt = request.prompt
    
    # --- ÉTAPE 1 : ROUTING (LLM Décide) ---
    # Le LLM décide s'il faut chercher un film
    raw_response = await llm_service.generate_response(user_prompt)
    
    # --- ÉTAPE 2 : DÉTECTION D'OUTIL ---
    # On cherche le pattern JSON strict
    json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)

    if json_match:
        try:
            # Parsing de la demande du LLM
            data = json.loads(json_match.group())
            tool_request = ToolCall(**data)

            if tool_request.action == "get_movie_data":
                movie_title = tool_request.parameters.get("title")
                print(f"[*] Recherche active pour : {movie_title}")

                # --- ÉTAPE 3 : ORCHESTRATION (La connexion Base/Scrape) ---
                
                # A. Recherche (Cache Local OU Scrape Live via mcp.py)
                # Note: Assure-toi que search_movie dans mcp.py est 'async' 
                # sinon enlève le 'await'
                search_results = await mcp_tools.search_movie(movie_title, limit=1)
                
                tool_result = {}
                
                if not search_results:
                    tool_result = {"found": False, "message": "Film introuvable sur les plateformes suivies."}
                else:
                    # B. Récupération des détails (Si trouvé)
                    best_match = search_results[0]
                    movie_id = best_match.get("id") or best_match.get("internal_id")
                    
                    # Récupération fiche complète (Note, Streaming, etc.)
                    full_details = await mcp_tools.get_movie(movie_id)
                    tool_result = full_details

                # --- ÉTAPE 4 : SYNTHÈSE (Réponse à l'utilisateur) ---
                writer_system_prompt = """
                Tu es Popcorn 🍿, l'expert cinéma. 
                Utilise les DONNÉES TECHNIQUES ci-dessous pour répondre à l'utilisateur.
                - Si le film est trouvé : Donne le titre, l'année, la note et les plateformes.
                - Si pas trouvé : Excuse-toi poliment.
                - Sois court, punchy et utile. Pas de blabla.
                """
                
                final_context = (
                    f"Question User: '{user_prompt}'\n"
                    f"Données Outil (Prioritaires): {json.dumps(tool_result, ensure_ascii=False)}"
                )
                
                final_answer = await llm_service.generate_response(
                    user_prompt=final_context, 
                    system_instruction=writer_system_prompt
                )
                
                return {
                    "response": final_answer, 
                    "debug_tool": tool_result # Utile pour le Front (MovieCard)
                }

        except Exception as e:
            print(f"[!] Erreur Pipeline: {e}")
            return {"response": "Oups, petit souci technique en allant chercher les infos 🍿."}

    # Cas standard (Conversation)
    return {"response": raw_response}