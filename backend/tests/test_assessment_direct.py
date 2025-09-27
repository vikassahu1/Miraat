#!/usr/bin/env python3
"""
Direct Assessment Form Rendering Test
This allows you to test the assessment form rendering without going through the entire conversation flow.
"""

import sys
from pathlib import Path
import json

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.append(str(backend_dir))

from fastapi.testclient import TestClient
from main import app

def create_mock_session_data(category_name="Generalized_Anxiety_Disorder"):
    """Create a mock session data object ready for assessment"""
    return {
        "session_id": "test-session-123",
        "status": "assessing",
        "ai_question_to_ask_user": None,
        "conversation_history": [
            {"role": "user", "content": "I've been feeling very anxious lately"},
            {"role": "assistant", "content": "I understand that must be difficult. Can you tell me more?"},
            {"role": "user", "content": "I worry about everything and feel nervous around people"},
            {"role": "assistant", "content": "Thank you for sharing. Based on our conversation, I'd like to understand more through a brief assessment."}
        ],
        "belief_state": {
            category_name: 0.95,
            "Social_Anxiety_Disorder": 0.05
        },
        "final_category": category_name,
        "assessment_data": None
    }

def test_assessment_form_direct():
    """Test assessment form rendering directly by simulating assessment_ready status"""
    print("🧪 Testing Assessment Form Rendering (Direct Method)")
    print("=" * 60)
    
    client = TestClient(app)
    
    # Test different categories
    categories_to_test = [
        "Generalized_Anxiety_Disorder",
        "Social_Anxiety_Disorder", 
        "Major_Depressive_Disorder"
    ]
    
    for category in categories_to_test:
        print(f"\n--- Testing Category: {category} ---")
        
        try:
            # Create mock session data for this category
            mock_session = create_mock_session_data(category)
            
            # Create a mock conversation response that triggers assessment
            # We'll simulate what happens when respond_conversation_logic returns assessment_ready
            mock_response_data = {
                "user_input": "This really affects my daily life significantly",
                "session_data_json": json.dumps(mock_session)
            }
            
            # We need to directly test the assessment service first
            print("   Testing assessment service...")
            
            # Import the services to test them directly
            from app.services.assessment_service import AssessmentService
            from app.services.report_service import FinalReportService
            
            # Load the required data
            KB_PATH = backend_dir / 'core_logic' / 'Assessment' / 'mapping.json'
            ABBR_PATH = backend_dir / 'core_logic' / 'Assessment' / 'abbreviation_map.json'
            TESTDATA_PATH = backend_dir / 'core_logic' / 'Assessment' / 'test_data.json'
            
            with open(KB_PATH) as f:
                knowledge_base = json.load(f)["Mental_Health_Tests"]
            with open(ABBR_PATH) as f:
                abbr_map = json.load(f)
            with open(TESTDATA_PATH) as f:
                test_data = json.load(f)
            
            report_service = FinalReportService()
            assessment_service = AssessmentService(
                knowledge_base=knowledge_base,
                test_data=test_data,
                abbr_map=abbr_map,
                report_service=report_service
            )
            
            # Test getting assessment data
            test_data_result = assessment_service.get_assessment_for_category(category)
            print(f"   ✅ Found test: {test_data_result.test_name}")
            print(f"   ✅ Questions: {len(test_data_result.test_data)}")
            
            # Now test the template rendering
            from fastapi.templating import Jinja2Templates
            from fastapi import Request
            
            templates = Jinja2Templates(directory="templates")
            
            # Create a mock request object
            class MockRequest:
                pass
            
            mock_request = MockRequest()
            
            # Test template rendering
            try:
                response = templates.TemplateResponse("partials/assessment_form.html", {
                    "request": mock_request,
                    "session_data": mock_session,
                    "test_data": test_data_result.model_dump()
                })
                print(f"   ✅ Template renders successfully")
                print(f"   ✅ HTML length: {len(response.body)} bytes")
                
            except Exception as template_error:
                print(f"   ❌ Template rendering error: {template_error}")
                
        except Exception as e:
            print(f"   ❌ Error testing {category}: {e}")
    
    return True

def create_assessment_test_endpoint():
    """Create a special test endpoint for assessment form rendering"""
    print("\n🔧 Creating Assessment Test Endpoint")
    print("=" * 60)
    
    test_endpoint_code = '''
# Add this to your ui.py for testing purposes (remove in production)

@router.get("/test_assessment/{category}", response_class=HTMLResponse)
async def test_assessment_form(
    request: Request,
    category: str,
    assessment_service: AssessmentService = Depends(get_assessment_service)
):
    """Test endpoint to directly render assessment form for any category"""
    logging.info(f"[TEST] Testing assessment form for category: {category}")
    
    try:
        # Get test data
        test_data = assessment_service.get_assessment_for_category(category)
        
        # Create mock session data
        mock_session_data = {
            "session_id": "test-session",
            "status": "assessing", 
            "final_category": category,
            "conversation_history": [
                {"role": "user", "content": "Test conversation"},
                {"role": "assistant", "content": "Test response"}
            ]
        }
        
        return templates.TemplateResponse("partials/assessment_form.html", {
            "request": request,
            "session_data": mock_session_data,
            "test_data": test_data.model_dump()
        })
        
    except Exception as e:
        error_html = f"""
        <div class="p-4 bg-red-50 border border-red-200 rounded-lg">
            <h3 class="text-red-800">Test Error</h3>
            <p class="text-red-700">Error testing category "{category}": {str(e)}</p>
        </div>
        """
        return HTMLResponse(error_html)
'''
    
    print("Add this endpoint to your ui.py file to test assessment forms directly:")
    print(test_endpoint_code)
    print("\nThen you can visit URLs like:")
    print("  http://localhost:8000/ui/test_assessment/Generalized_Anxiety_Disorder")
    print("  http://localhost:8000/ui/test_assessment/Social_Anxiety_Disorder")
    print("  http://localhost:8000/ui/test_assessment/Major_Depressive_Disorder")

def test_assessment_submission():
    """Test the assessment submission process with mock data"""
    print("\n🧪 Testing Assessment Submission")
    print("=" * 40)
    
    client = TestClient(app)
    
    # Create mock session data with assessment ready
    mock_session = create_mock_session_data("Generalized_Anxiety_Disorder")
    mock_session["status"] = "assessing"
    
    # Create mock answers (typical GAD-7 responses)
    mock_answers = {
        "question_1": "2",
        "question_2": "1", 
        "question_3": "3",
        "question_4": "2",
        "question_5": "1",
        "question_6": "2",
        "question_7": "2"
    }
    
    # Prepare form data
    form_data = {
        "session_data_json": json.dumps(mock_session),
        **mock_answers
    }
    
    print("Testing assessment submission...")
    response = client.post("/ui/submit_assessment", data=form_data)
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("✅ Assessment submission successful")
        if "opening_summary" in response.text:
            print("✅ Final report detected in response")
        else:
            print("⚠️  Response doesn't contain expected report structure")
    else:
        print(f"❌ Assessment submission failed")
        print(f"Response: {response.text[:500]}...")

if __name__ == "__main__":
    print("🚀 Assessment Form Testing Suite")
    print("=" * 60)
    
    try:
        # Test 1: Direct assessment form rendering
        test_assessment_form_direct()
        
        # Test 2: Show how to create test endpoint
        create_assessment_test_endpoint()
        
        # Test 3: Test assessment submission
        test_assessment_submission()
        
        print("\n🎉 All tests completed!")
        print("\nQuick Testing Tips:")
        print("1. Add the test endpoint to ui.py for quick form testing")
        print("2. Use the direct testing functions to validate assessment logic")
        print("3. Test different categories by changing the category parameter")
        
    except Exception as e:
        print(f"\n💥 Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)