#!/usr/bin/env python3
"""
Test the subcategory refinement to assessment transition
"""

import sys
from pathlib import Path
import json

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.append(str(backend_dir))

def test_subcategory_completion():
    """Test that subcategory refinement properly transitions to assessment"""
    print("🧪 Testing Subcategory to Assessment Transition")
    print("=" * 60)
    
    try:
        from app.services.conversation_service import ConversationService
        from app.services.config import SUBCATEGORY_THRESHOLD
        
        # Load knowledge base
        KB_PATH = backend_dir / 'core_logic' / 'Assessment' / 'mapping.json'
        with open(KB_PATH) as f:
            knowledge_base = json.load(f)["Mental_Health_Tests"]
        
        convo_service = ConversationService(knowledge_base=knowledge_base)
        
        # Test the check_funnel_completion with subcategory data
        test_session = {
            'status': 'refining_sub',
            'belief_state': {
                'Generalized_Anxiety_Disorder': 0.85,  # Above threshold
                'Social_Anxiety_Disorder': 0.15
            }
        }
        
        print(f"Subcategory threshold: {SUBCATEGORY_THRESHOLD}")
        print(f"Test belief state: {test_session['belief_state']}")
        
        result = convo_service.check_funnel_completion(test_session)
        print(f"Check funnel completion result: {result}")
        
        if result == 'Generalized_Anxiety_Disorder':
            print("✅ Subcategory completion check works correctly")
        else:
            print("❌ Subcategory completion check failed")
            return False
        
        # Test the assessment service lookup
        print("\n--- Testing Assessment Service Lookup ---")
        from app.services.assessment_service import AssessmentService
        from app.services.report_service import FinalReportService
        
        # Load test data
        ABBR_PATH = backend_dir / 'core_logic' / 'Assessment' / 'abbreviation_map.json'
        TESTDATA_PATH = backend_dir / 'core_logic' / 'Assessment' / 'test_data.json'
        
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
        
        try:
            test_data_result = assessment_service.get_assessment_for_category('Generalized_Anxiety_Disorder')
            print(f"✅ Assessment service found test: {test_data_result.test_name}")
            print(f"   Number of questions: {len(test_data_result.test_data)}")
            return True
        except Exception as e:
            print(f"❌ Assessment service error: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_subcategory_completion()
    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n💥 Tests failed!")
        sys.exit(1)