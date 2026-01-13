import json
import re
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, List, Any

from app.services.llm_service import llm_service

router = APIRouter(prefix="/chat", tags=["AI"])

# --- MÉMOIRE GLOBALE (Contexte) ---
conversation_history = [] 

# --- MODÈLES ---
class ChatRequest(BaseModel):
    prompt: str

class ToolCall(BaseModel):
    action: str
    parameters: Dict[str, Any]

# --- OUTIL SIMULÉ ---
async def get_movie_data_placeholder(title: str) -> Dict:
    print(f"    [TOOL] Recherche pour: {title}")
    # Données simulées (Ce sera ton scraper demain)
    return {
        "title": title,
        "year": 2010,
        "rating": 8.8,
        "director": "Christopher Nolan",
        "synopsis": "Un voleur qui vole des secrets d'entreprise à travers l'utilisation de la technologie de partage de rêves...",
        "platforms": ["Netflix", "HBO"]
    }

# --- ROUTEUR PRINCIPAL ---
@router.post("/")
async def ask_hephaestus(request: ChatRequest):
    global conversation_history
    user_prompt = request.prompt

    # 1. Ajout à la mémoire
    conversation_history.append({"role": "user", "content": user_prompt})
    
    # 2. L'IA réfléchit (peut générer du JSON)
    # On envoie l'historique pour qu'elle comprenne "sa note" = "note de Titanic"
    raw_response = await llm_service.generate_response(conversation_history)
    
    # Par défaut, on suppose que c'est du texte. 
    # Si c'est du JSON, on va l'écraser par la synthèse plus bas.
    final_text_response = raw_response 
    tool_data = None

    # 3. Détection JSON (Invisible pour l'utilisateur)
    json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)

    if json_match:
        try:
            # Nettoyage
            clean_json = json_match.group()
            start = clean_json.find('{')
            end = clean_json.rfind('}') + 1
            data = json.loads(clean_json[start:end])
            
            tool_request = ToolCall(**data)

            if tool_request.action == "get_movie_data":
                # Récupération du titre (même s'il n'était pas dans le dernier prompt)
                movie_title = tool_request.parameters.get("title")
                
                # EXÉCUTION (Backend only)
                tool_data = await get_movie_data_placeholder(movie_title)
                
                # SYNTHÈSE (Transformation JSON -> Phrase)
                # C'est ici qu'on "cache" le JSON à l'utilisateur
                synthesis_prompt = (
                    f"Voici la FICHE TECHNIQUE OFFICIELLE (Réalité de terrain) : {tool_data}. "
                    f"L'utilisateur veut savoir : '{user_prompt}'. "
                    "CONSIGNES : "
                    "1. Utilise UNIQUEMENT les infos de la fiche technique ci-dessus."
                    "2. N'invente rien (pas de suite imaginaire, pas de fausses dates)."
                    "3. Fais une réponse courte, enthousiaste et donne envie de voir le film."
                )
                
                # On force l'IA à changer de personnalité
                final_text_response = await llm_service.generate_response(
                    [{"role": "user", "content": synthesis_prompt}], 
                    system_instruction="Tu es un critique cinéma expert et factuel. Tu ne parles jamais de technique, juste du film."
                )

        except Exception as e:
            print(f"[!] Erreur Tooling: {e}")

    # 4. Sauvegarde de la réponse PROPRE (pas le JSON) dans l'historique
    conversation_history.append({"role": "assistant", "content": final_text_response})

    # 5. Envoi au Frontend
    return {
        "response": final_text_response,  # <-- C'est LA PHRASE (ex: "Inception est noté 8.8...")
        "media": {                        # <-- C'est pour afficher la belle image (optionnel)
            "type": "movie_result",
            "data": tool_data
        } if tool_data else None
    }