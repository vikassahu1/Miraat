#!/usr/bin/env python3
"""
Quick test to check if test endpoints are working
"""

import sys
from pathlib import Path
import json

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.append(str(backend_dir))

from fastapi.testclient import TestClient

def test_endpoints():
    """Test the endpoints directly"""
    print("🧪 Testing Assessment Endpoints")
    print("=" * 50)
    
    try:
        from main import app
        client = TestClient(app)
        
        # Test 1: Test categories endpoint
        print("\n--- Testing /ui/test_categories ---")
        response = client.get("/ui/test_categories")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Test categories endpoint working")
            print(f"Response length: {len(response.text)} chars")
        else:
            print(f"❌ Test categories failed: {response.text[:200]}")
        
        # Test 2: Test dashboard endpoint
        print("\n--- Testing /ui/test_dashboard ---")
        response = client.get("/ui/test_dashboard")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Test dashboard endpoint working")
        else:
            print(f"❌ Test dashboard failed: {response.text[:200]}")
        
        # Test 3: Test assessment form endpoint
        print("\n--- Testing /ui/test_assessment/Generalized_Anxiety_Disorder ---")
        response = client.get("/ui/test_assessment/Generalized_Anxiety_Disorder")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Test assessment form working")
            if "test_name" in response.text or "assessment" in response.text.lower():
                print("✅ Form content detected")
            else:
                print("⚠️  Form content might be missing")
        else:
            print(f"❌ Test assessment failed: {response.text[:500]}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error testing endpoints: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_endpoints()