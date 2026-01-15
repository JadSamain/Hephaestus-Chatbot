import ollama

# Prompt pour le routeur
ROUTER_SYSTEM_PROMPT = """
Tu es un automate. Si l'utilisateur parle d'un film, réponds UNIQUEMENT avec ce JSON :
{"action": "get_movie_data", "parameters": {"title": "NOM DU FILM"}}
Ne réponds RIEN d'autre. Pas de texte avant, pas de texte après.
"""

class LLMService:
    def __init__(self):
        self.model = "Hephaestus-v1" 

    async def generate_response(self, user_prompt: str, system_instruction: str = None) -> str:
        """
        Génère une réponse. 
        Si system_instruction est vide, on utilise le ROUTER_SYSTEM_PROMPT par défaut.
        """
        # Choix du prompt système : soit celui passé en paramètre (pour la synthèse), soit le routeur (par défaut)
        active_system_prompt = system_instruction if system_instruction else ROUTER_SYSTEM_PROMPT

        try:
            response = ollama.chat(model=self.model, messages=[
                {'role': 'system', 'content': active_system_prompt},
                {'role': 'user', 'content': user_prompt},
            ], options={'temperature': 0.1}) # Température basse pour la précision du JSON pour s'assurer de proposer une réponse tout de même
            
            return response['message']['content']
        except Exception as e:
            return f"Erreur critique Ollama: {str(e)}"

llm_service = LLMService()