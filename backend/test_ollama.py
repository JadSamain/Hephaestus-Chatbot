import asyncio
from app.services.llm_service import llm_service

async def main():
    print("--- Test de connexion Ollama ---")
    prompt = "Hello, are you ready to act as a backend assistant?"
    
    # Appel asynchrone
    response = await llm_service.generate_response(prompt)
    
    print("\n--- Réponse reçue ---")
    print(response)
    print("---------------------")

if __name__ == "__main__":
    asyncio.run(main())