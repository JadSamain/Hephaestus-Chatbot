import sys
sys.path.insert(0, 'c:/Users/moham/Desktop/CHATBOT/Hephaestus-Chatbot/backend')

from app.main import app

print("App routes:")
for route in app.routes:
    print(f"  {route.path}")
