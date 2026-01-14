import sys
sys.path.insert(0, 'c:/Users/moham/Desktop/CHATBOT/Hephaestus-Chatbot/backend')

print("=== Testing Backend Routes ===\n")

# Test 1: Import main app
try:
    from app.main import app
    print("[OK] Main app imported successfully")
except Exception as e:
    print(f"[FAIL] Failed to import main app: {e}")
    sys.exit(1)

# Test 2: Check routes
print("\n=== Registered Routes ===")
for route in app.routes:
    if hasattr(route, 'path'):
        methods = getattr(route, 'methods', ['GET'])
        print(f"  {list(methods)[0] if methods else 'GET'} {route.path}")

# Test 3: Try to call the endpoint directly
print("\n=== Testing /films/platforms endpoint ===")
try:
    from app.services.movies_service import movies_service
    platforms = movies_service.get_available_platforms()
    print(f"[OK] Service works: {len(platforms)} platforms found")
    print(f"  Platforms: {platforms[:5]}...")
except Exception as e:
    print(f"[FAIL] Service failed: {e}")

# Test 4: Test the router directly
print("\n=== Testing router import ===")
try:
    from app.routers import films
    print(f"[OK] Router imported successfully")
    print(f"  Router prefix: {films.router.prefix}")
    print(f"  Router routes: {[r.path for r in films.router.routes]}")
except Exception as e:
    print(f"[FAIL] Router import failed: {e}")

# Test 5: Make a test request
print("\n=== Making test request ===")
try:
    from fastapi.testclient import TestClient
    client = TestClient(app)
    response = client.get("/films/platforms")
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.json()}")
except Exception as e:
    print(f"[FAIL] Test request failed: {e}")
