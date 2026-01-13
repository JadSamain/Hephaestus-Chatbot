import ollama

# --- PROMPT SPÉCIALISÉ POUR LE ROUTAGE (Step 1) ---
ROUTER_SYSTEM_PROMPT = """
Tu es un ROUTEUR API strict. Ton unique but est de classifier la demande.

RÈGLES ABSOLUES :
1. Si l'utilisateur demande des infos sur un film (acteurs, résumé, note), retourne UNIQUEMENT ce JSON :
   {"action": "get_movie_data", "parameters": {"title": "Titre Exact"}}

2. Si l'utilisateur dit bonjour ou parle d'autre chose, réponds poliment en texte brut.

3. INTERDIT : Ne raconte JAMAIS l'histoire du film. Ne donne PAS ton avis. Ne mets PAS de balises Markdown (```json).
Juste le JSON brut.

EXEMPLES :
User: "Parle moi de Avatar"
Assistant: {"action": "get_movie_data", "parameters": {"title": "Avatar"}}

User: "Bonjour ça va ?"
Assistant: Bonjour ! Je suis prêt à parler cinéma.
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
            ], options={'temperature': 0.1}) # Température basse pour la précision du JSON
            
            return response['message']['content']
        except Exception as e:
            return f"Erreur critique Ollama: {str(e)}"

llm_service = LLMService()