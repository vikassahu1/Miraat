#!/usr/bin/env python3
"""
Simple test script to verify the UI flow works correctly
"""

import sys
import os
import json
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.append(str(backend_dir))

# Test imports
print("Testing imports...")
try:
    from app.services.schemas import SessionData, StartRequest, RespondRequest
    from app.logic.conversation import start_conversation, respond_conversation
    from app.services.conversation_service import ConversationService
    from app.services.triage_service import TriageService
    from app.services.assessment_service import AssessmentService
    from app.services.report_service import FinalReportService
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def load_test_data():
    """Load the knowledge base and test data"""
    print("\nLoading test data...")
    
    KB_PATH = backend_dir / 'core_logic' / 'Assessment' / 'mapping.json'
    ABBR_PATH = backend_dir / 'core_logic' / 'Assessment' / 'abbreviation_map.json'
    TESTDATA_PATH = backend_dir / 'core_logic' / 'Assessment' / 'test_data.json'
    
    try:
        with open(KB_PATH) as f:
            knowledge_base = json.load(f)["Mental_Health_Tests"]
        
        with open(ABBR_PATH) as f:
            abbr_map = json.load(f)
        
        with open(TESTDATA_PATH) as f:
            test_data = json.load(f)
        
        print("✅ Test data loaded successfully")
        return knowledge_base, abbr_map, test_data
    
    except FileNotFoundError as e:
        print(f"❌ Failed to load test data: {e}")
        sys.exit(1)

def create_services(knowledge_base, abbr_map, test_data):
    """Create service instances"""
    print("\nCreating service instances...")
    
    try:
        convo_service = ConversationService(knowledge_base=knowledge_base)
        triage_service = TriageService(categories=list(knowledge_base.keys()))
        report_service = FinalReportService()
        assessment_service = AssessmentService(
            knowledge_base=knowledge_base, 
            test_data=test_data, 
            abbr_map=abbr_map, 
            report_service=report_service
        )
        
        print("✅ Services created successfully")
        return convo_service, triage_service, assessment_service, report_service
    
    except Exception as e:
        print(f"❌ Failed to create services: {e}")
        sys.exit(1)

def test_conversation_start(convo_service):
    """Test conversation start"""
    print("\n--- Testing Conversation Start ---")
    
    try:
        start_request = StartRequest(
            initial_text="I've been feeling really anxious and worried lately", 
            consent_given=True
        )
        
        start_response = start_conversation(start_request, convo_service)
        print(f"✅ Conversation started successfully")
        print(f"   AI Question: {start_response.ai_question[:50]}...")
        print(f"   Session ID: {start_response.session_data.session_id}")
        print(f"   Status: {start_response.session_data.status}")
        
        return start_response.session_data
    
    except Exception as e:
        print(f"❌ Conversation start failed: {e}")
        return None

def test_conversation_continue(session_data, convo_service, triage_service):
    """Test conversation continuation"""
    print("\n--- Testing Conversation Continue ---")
    
    try:
        respond_request = RespondRequest(
            user_answer="It's affecting my sleep and I worry about everything",
            session_data=session_data
        )
        
        respond_result = respond_conversation(respond_request, convo_service, triage_service)
        
        print(f"✅ Conversation continued successfully")
        print(f"   Status: {respond_result.status}")
        
        if respond_result.ai_question:
            print(f"   Next Question: {respond_result.ai_question[:50]}...")
        
        return respond_result.session_data
    
    except Exception as e:
        print(f"❌ Conversation continue failed: {e}")
        return None

if __name__ == "__main__":
    print("🧪 Starting UI Flow Test")
    print("=" * 50)
    
    # Load data
    knowledge_base, abbr_map, test_data = load_test_data()
    
    # Create services
    convo_service, triage_service, assessment_service, report_service = create_services(
        knowledge_base, abbr_map, test_data
    )
    
    # Test conversation start
    session_data = test_conversation_start(convo_service)
    if not session_data:
        sys.exit(1)
    
    # Test conversation continue
    updated_session = test_conversation_continue(session_data, convo_service, triage_service)
    if not updated_session:
        sys.exit(1)
    
    print("\n🎉 Basic flow test completed successfully!")
    print("=" * 50)
    
    print(f"\nFinal session status: {updated_session.status}")
    if updated_session.belief_state:
        print("Current belief state:")
        for category, confidence in updated_session.belief_state.items():
            print(f"  - {category}: {confidence:.2f}")