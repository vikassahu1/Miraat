#!/usr/bin/env python3
"""
Test the complete conversation flow including the transition to assessment
"""

import sys
from pathlib import Path
import json
import re

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.append(str(backend_dir))

from fastapi.testclient import TestClient
from main import app

def extract_session_data_from_html(html_content):
    """Extract session data JSON from HTML response"""
    pattern = r"name=['\"]session_data_json['\"] value='([^']*?)'"
    match = re.search(pattern, html_content)
    if match:
        json_str = match.group(1)
        # Unescape HTML entities
        json_str = json_str.replace("&quot;", '"').replace("&#39;", "'").replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
        return json.loads(json_str)
    return None

def test_complete_conversation_flow():
    """Test the complete conversation flow from start to assessment"""
    print("🧪 Testing Complete Conversation Flow")
    print("=" * 60)
    
    client = TestClient(app)
    
    # Step 1: Start conversation
    print("\n--- Step 1: Starting Conversation ---")
    response = client.post("/ui/conversation_turn", data={
        "user_input": "I've been feeling very anxious and worried lately"
    })
    
    if response.status_code != 200:
        print(f"❌ Failed to start conversation: {response.status_code}")
        return False
    
    print("✅ Conversation started")
    session_data = extract_session_data_from_html(response.text)
    if not session_data:
        print("❌ Could not extract session data from initial response")
        return False
    
    print(f"   Session ID: {session_data['session_id']}")
    print(f"   Status: {session_data['status']}")
    
    # Step 2: Continue conversation to trigger triage
    print("\n--- Step 2: Providing More Details ---")
    response = client.post("/ui/conversation_turn", data={
        "user_input": "I feel anxious around people, especially in social situations",
        "session_data_json": json.dumps(session_data)
    })
    
    if response.status_code != 200:
        print(f"❌ Failed at step 2: {response.status_code}")
        return False
    
    session_data = extract_session_data_from_html(response.text)
    if not session_data:
        print("❌ Could not extract session data from step 2")
        return False
    
    print(f"✅ Step 2 completed")
    print(f"   Status: {session_data['status']}")
    if session_data.get('belief_state'):
        print(f"   Belief state: {session_data['belief_state']}")
    
    # Step 3: Continue to trigger subcategory refinement
    print("\n--- Step 3: Triggering Subcategory Refinement ---")
    response = client.post("/ui/conversation_turn", data={
        "user_input": "Yes, I feel like people are judging me and I get very nervous in groups",
        "session_data_json": json.dumps(session_data)
    })
    
    if response.status_code != 200:
        print(f"❌ Failed at step 3: {response.status_code}")
        return False
    
    session_data = extract_session_data_from_html(response.text)
    if not session_data:
        print("❌ Could not extract session data from step 3")
        return False
    
    print(f"✅ Step 3 completed")
    print(f"   Status: {session_data['status']}")
    if session_data.get('belief_state'):
        print(f"   Belief state: {session_data['belief_state']}")
    
    # Step 4: Try to trigger assessment (may need multiple attempts)
    for attempt in range(3):
        print(f"\n--- Step 4.{attempt+1}: Attempting to Trigger Assessment ---")
        response = client.post("/ui/conversation_turn", data={
            "user_input": f"Yes, this happens very frequently and it's really affecting my daily life. I avoid social situations because of this anxiety. {attempt}",
            "session_data_json": json.dumps(session_data)
        })
        
        if response.status_code != 200:
            print(f"❌ Failed at step 4.{attempt+1}: {response.status_code}")
            print(f"Response: {response.text[:500]}...")
            continue
        
        # Check if we got an assessment form
        if "assessment" in response.text.lower() or "test" in response.text.lower():
            print("✅ Assessment form detected!")
            return True
        
        # Update session data for next attempt
        new_session_data = extract_session_data_from_html(response.text)
        if new_session_data:
            session_data = new_session_data
            print(f"   Status: {session_data['status']}")
            if session_data.get('belief_state'):
                print(f"   Belief state: {session_data['belief_state']}")
            
            # Check if we reached final category
            if session_data.get('final_category'):
                print(f"   Final category: {session_data['final_category']}")
                if session_data.get('status') == 'assessing':
                    print("✅ Reached assessment phase!")
                    return True
    
    print("⚠️  Did not reach assessment phase after 3 attempts")
    return False

if __name__ == "__main__":
    success = test_complete_conversation_flow()
    if success:
        print("\n🎉 Complete conversation flow test passed!")
    else:
        print("\n💥 Complete conversation flow test failed!")
        sys.exit(1)