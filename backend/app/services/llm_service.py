import ollama
from ollama import AsyncClient

class LLMService:
    def __init__(self, model: str = "Hephaestus-v1"):
        self.model = model
        self.client = AsyncClient(host='http://localhost:11434')

    async def generate_response(self, prompt: str) -> str:
        try:
            # print(f"[*] Debug: Envoi à {self.model}")
            response = await self.client.chat(model=self.model, messages=[
                {
                    'role': 'user',
                    'content': prompt,
                },
            ])
            return response['message']['content']
        except Exception as e:
            print(f"[!] Erreur Ollama: {e}")
            return f"Erreur critique: Impossible de joindre Ollama ou le modèle '{self.model}' n'existe pas."

# Instance globale
llm_service = LLMService()
