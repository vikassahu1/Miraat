#!/usr/bin/env python3
"""
Test the FastAPI UI endpoints to make sure they work correctly
"""

import sys
from pathlib import Path
import json

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.append(str(backend_dir))

from fastapi.testclient import TestClient
from main import app

def test_endpoints():
    """Test the UI endpoints"""
    print("🧪 Testing FastAPI UI Endpoints")
    print("=" * 50)
    
    client = TestClient(app)
    
    # Test 1: GET /hi (main page)
    print("\n--- Testing GET /hi ---")
    response = client.get("/hi")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Main page loads successfully")
    else:
        print(f"❌ Main page failed: {response.text}")
        return False
    
    # Test 2: GET /ui/initial_chat_view
    print("\n--- Testing GET /ui/initial_chat_view ---")
    response = client.get("/ui/initial_chat_view")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Initial chat view loads successfully")
        print(f"   Response length: {len(response.text)} characters")
    else:
        print(f"❌ Initial chat view failed: {response.text}")
        return False
    
    # Test 3: GET /ui/welcome_view
    print("\n--- Testing GET /ui/welcome_view ---")
    response = client.get("/ui/welcome_view")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Welcome view loads successfully")
    else:
        print(f"❌ Welcome view failed: {response.text}")
        return False
    
    # Test 4: POST /ui/conversation_turn (initial)
    print("\n--- Testing POST /ui/conversation_turn (initial) ---")
    response = client.post("/ui/conversation_turn", data={
        "user_input": "I've been feeling very anxious lately and can't sleep well"
    })
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Initial conversation turn successful")
        # Extract session data from response for next test
        if "session_data" in response.text:
            print("✅ Session data found in response")
        else:
            print("⚠️  Session data not found in response")
    else:
        print(f"❌ Initial conversation turn failed: {response.text}")
        return False
    
    print("\n🎉 All endpoint tests completed successfully!")
    return True

if __name__ == "__main__":
    success = test_endpoints()
    if not success:
        sys.exit(1)
    print("\n✅ UI endpoints are working correctly!")