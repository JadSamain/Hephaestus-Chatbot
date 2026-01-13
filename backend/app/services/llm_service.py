import ollama
from typing import List, Dict

# Prompt par défaut (Mode "Robot JSON strict")
DEFAULT_SYSTEM_PROMPT = """
Tu es le cerveau backend de 'Popcorn'.
RÈGLES :
1. Si l'utilisateur demande une info sur un film, réponds UNIQUEMENT avec ce JSON : {"action": "get_movie_data", "parameters": {"title": "Titre"}}
2. NE PARLE PAS. RIEN D'AUTRE QUE LE JSON.
3. Si c'est juste une conversation ("Bonjour", "Merci"), réponds que tu ne sais que parler de cinéma. Réponds gentillement, mais fais comprendre à l'utilisateur que ton but n'est pas de parler d'autre chose que de cinéma.
"""

class LLMService:
    def __init__(self):
        self.model = "Hephaestus-v1" 

    async def generate_response(self, conversation_history: List[Dict[str, str]], system_instruction: str = None) -> str:
        """
        Envoie tout l'historique de conversation à Ollama.
        """
        # On définit le System Prompt actif
        active_system = system_instruction if system_instruction else DEFAULT_SYSTEM_PROMPT
        
        # On construit la liste complète : [SYSTEM] + [HISTORIQUE]
        full_messages = [{'role': 'system', 'content': active_system}] + conversation_history
        
        try:
            print(f"    [LLM] Envoi de {len(full_messages)} messages au modèle.")
            response = ollama.chat(model=self.model, messages=full_messages)
            return response['message']['content']
        except Exception as e:
            return f"Erreur LLM: {str(e)}"

llm_service = LLMService()