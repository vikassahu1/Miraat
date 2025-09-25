# app/services/assessment_service.py
from app.services.schemas import SessionData, Pair, TestData, QuestionData, AssessmentReport
from app.services.report_service import FinalReportService
from core_logic.Assessment.test_inference import get_inference
from core_logic.Accessories.logger import logging
import json
import os 


class AssessmentService:
    def __init__(self, knowledge_base: dict, test_data: dict, abbr_map: dict,report_service: FinalReportService):
        self.knowledge_base = knowledge_base
        self.test_data = test_data
        self.abbr_map = abbr_map
        self.report_service = report_service

    def _get_testname_and_abbreviation(self, disorder_name: str) -> Pair:
        """
        Given a disorder (subcategory) name, return the test name for it from the knowledge base.
        """
        test_name = None 
        for _ , cat_data in self.knowledge_base.items():
            subcats = cat_data.get("Subcategories", {})
            if disorder_name in subcats:
                tests = subcats[disorder_name].get("Tests", [])
                if tests:
                    test_name = tests[0]  # Return the first test name
        

        abbreviation = self.abbr_map.get(disorder_name)

        return Pair(first = test_name,second = abbreviation)
        



    def get_assessment_for_category(self, final_category: str) -> TestData:
        """
        Looks up the full test (name, questions, scoring options) for a given category.
        This is called by the /start endpoint.
        """
        pair = self._get_testname_and_abbreviation(final_category)
        test_name = pair.first
        abbreviation = pair.second

        # Get the raw question list from test_data
        raw_questions = self.test_data.get(abbreviation, []) if abbreviation else []

        # Convert each dict to a QuestionData object
        questions = [QuestionData(**q) for q in raw_questions]

        print(f"Fetching full test for category: {final_category}")

        return TestData(
            test_name=test_name if test_name else "Unknown Test",
            test_data=questions
        )



    
    def score_and_conclude_assessment(self, session_data: SessionData, answers: dict) -> SessionData:
        """
        Score the assessment and generate the final report
        """
        logging.info(f"[AssessmentService] Scoring assessment for category: {session_data.final_category}")
        logging.info(f"[AssessmentService] Received answers: {answers}")
        
        # Get the test info
        pair = self._get_testname_and_abbreviation(session_data.final_category)
        test_name = pair.first
        abbreviation = pair.second
        
        # Format answers for the inference function (it expects question numbers as keys)
        formatted_answers = {}
        for key, value in answers.items():
            # Extract question number from key like "question_1" -> 1
            if key.startswith("question_"):
                question_num = int(key.split("_")[1])
                formatted_answers[question_num] = value
        
        logging.info(f"[AssessmentService] Formatted answers for inference: {formatted_answers}")
        
        # Get the score and interpretation
        raw_score, score_interpretation = get_inference(abbreviation, formatted_answers)
        logging.info(f"[AssessmentService] Calculated raw score: {raw_score}, interpretation: {score_interpretation}")

        # Create the assessment report
        session_data.assessment_data = AssessmentReport(
            test_name=test_name if test_name else "Assessment", 
            answers=formatted_answers, 
            final_score=raw_score, 
            interpretation=score_interpretation,
            narrative_report=None  # Will be filled by report service
        )
        
        # Generate the final report using report service
        final_report = self.report_service.generate_final_report(session_data)
        session_data.assessment_data.narrative_report = final_report
        session_data.status = "complete"
        
        logging.info(f"[AssessmentService] Assessment completed successfully")
        return session_data
    



