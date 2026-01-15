import json
import requests

# Configuration Ollama
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "mistral"

# Mock du Scraper (Selenium serait ici)
def scrape_movie(movie_title):
    # Simulation d'un retour de scraping
    print(f"DEBUG: Scraping de {movie_title}...")
    if "inception" in movie_title.lower():
        return {
            "title": "Inception",
            "year": 2010,
            "rating": 8.8,
            "platforms": ["Netflix", "Canal+"],
            "found": True
        }
    return {"found": False}

# Dictionnaire des outils
TOOLS = {
    "get_movie_data": scrape_movie
}

def query_ollama(messages):
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
        "format": "json" # Force le mode JSON natif d'Ollama si supporté, sinon retirer
    }
    response = requests.post(OLLAMA_URL, json=payload)
    return response.json()["message"]["content"]

def chat_orchestrator(user_input, conversation_history):
    # 1. Préparation du contexte
    system_prompt = """
    Tu es Popcorn. Utilise {"tool": "get_movie_data", "args": "titre"} pour obtenir des infos. 
    Réponds en JSON uniquement si appel outil. Sinon texte brut.
    """
    
    # Ajout du message utilisateur
    conversation_history.append({"role": "user", "content": user_input})
    
    # Construction de la payload complète pour Ollama
    messages_payload = [{"role": "system", "content": system_prompt}] + conversation_history
    
    # Premier appel (Décision)
    raw_response = query_ollama(messages_payload)
    
    final_response_text = raw_response
    movie_data = None

    # Détection d'appel d'outil
    try:
        # Tentative de parsing JSON pour voir si c'est un outil
        tool_call = json.loads(raw_response)
        
        if "tool" in tool_call and tool_call["tool"] in TOOLS:
            tool_name = tool_call["tool"]
            args = tool_call["args"]
            
            # Exécution de l'outil
            tool_result = TOOLS[tool_name](args)
            movie_data = tool_result # Stockage pour le frontend
            
            # Injection du résultat (Context Injection)
            conversation_history.append({"role": "assistant", "content": raw_response})
            conversation_history.append({
                "role": "system", 
                "content": f"RÉSULTAT OUTIL: {json.dumps(tool_result)}. Utilise ces infos pour répondre à l'utilisateur."
            })
            
            # Deuxième appel (Synthèse finale)
            messages_payload = [{"role": "system", "content": system_prompt}] + conversation_history
            final_response_text = query_ollama(messages_payload)
            
    except json.JSONDecodeError:
        # Pas de JSON détecté, c'est une réponse conversationnelle directe
        pass

    # Mise à jour historique
    conversation_history.append({"role": "assistant", "content": final_response_text})

    # Formatage Sortie Frontend
    return build_frontend_response(final_response_text, movie_data)

def build_frontend_response(text_message, data=None):
    response = {
        "type": "text",
        "content": text_message,
        "meta": None
    }
    
    if data and data.get("found"):
        response["type"] = "movie_card"
        response["meta"] = {
            "title": data["title"],
            "rating": data["rating"],
            "availability": data["platforms"]
        }
        
    return response

# Test de l'agent
history = []
print(json.dumps(chat_orchestrator("Où voir Inception ?", history), indent=2))