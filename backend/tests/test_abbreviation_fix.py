#!/usr/bin/env python3
"""
Quick test to verify the abbreviation mapping fix
"""

import sys
from pathlib import Path
import json

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.append(str(backend_dir))

def test_abbreviation_mapping():
    """Test the abbreviation mapping fix"""
    print("🔍 Testing Abbreviation Mapping Fix")
    print("=" * 50)
    
    try:
        # Load the data files
        with open('core_logic/Assessment/mapping.json', 'r') as f:
            knowledge_base = json.load(f)["Mental_Health_Tests"]
        
        with open('core_logic/Assessment/abbreviation_map.json', 'r') as f:
            abbr_map = json.load(f)
        
        with open('core_logic/Assessment/test_data.json', 'r') as f:
            test_data = json.load(f)
        
        # Test the mapping for Social_Anxiety_Disorder
        disorder_name = "Social_Anxiety_Disorder"
        
        # Step 1: Get test name from knowledge base
        test_name = None
        for _, cat_data in knowledge_base.items():
            subcats = cat_data.get("Subcategories", {})
            if disorder_name in subcats:
                tests = subcats[disorder_name].get("Tests", [])
                if tests:
                    test_name = tests[0]
                    break
        
        print(f"Disorder: {disorder_name}")
        print(f"Test Name: {test_name}")
        
        # Step 2: Get abbreviation using test name
        abbreviation = abbr_map.get(test_name) if test_name else None
        print(f"Abbreviation: {abbreviation}")
        
        # Step 3: Check if test data exists
        questions = test_data.get(abbreviation, []) if abbreviation else []
        print(f"Questions found: {len(questions)}")
        
        if len(questions) > 0:
            print("✅ Abbreviation mapping is working!")
            print(f"First question: {questions[0]['question_text']}")
        else:
            print("❌ No questions found - mapping still broken")
            
        return len(questions) > 0
        
    except Exception as e:
        print(f"❌ Error testing mapping: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_abbreviation_mapping()