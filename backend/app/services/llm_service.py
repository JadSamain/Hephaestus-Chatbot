import ollama

# --- 1. DÉFINITION DU SYSTEM PROMPT ---
SYSTEM_PROMPT = """
Tu es l'intelligence centrale du backend "Popcorn".
Tu disposes de l'outil : `get_movie_data(title: string)`.

RÈGLES STRICTES :
1. Si l'utilisateur demande une info sur un film, tu DOIS répondre UNIQUEMENT avec le JSON de l'outil.
2. PAS de phrase d'intro. PAS d'explication. PAS de Markdown (```). JUSTE LE JSON BRUT.
3. Si la discussion est générale (pas de demande de film), réponds normalement en texte.

EXEMPLES À SUIVRE À LA LETTRE :

User: Parle-moi de Inception.
Assistant: {"action": "get_movie_data", "parameters": {"title": "Inception"}}

User : Tu connais Avatar ?
Assistant: {"action": "get_movie_data", "parameters": {"title": "Avatar"}}

C'est quoi The Godfather ?
Assistant: {"action": "get_movie_data", "parameters": {"title": "The Godfather"}}

User: Bonjour, ça va ?
Assistant: Bonjour ! Je suis prêt à parler cinéma.
"""

class LLMService:
    def __init__(self):
        # Assure-toi que le nom du modèle correspond à celui que tu as créé (Hephaestus-v1)
        self.model = "Hephaestus-v1"

    async def generate_response(self, user_prompt: str) -> str:
        """
        Envoie le prompt utilisateur à Ollama en injectant le System Prompt.
        """
        try:
            # On utilise le format 'chat' pour bien séparer le rôle system et user
            response = ollama.chat(model=self.model, messages=[
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user', 'content': user_prompt},
            ])
            return response['message']['content']
        except Exception as e:
            return f"Erreur critique Ollama: {str(e)}"

llm_service = LLMService()