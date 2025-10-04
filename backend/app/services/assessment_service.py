# app/services/assessment_service.py
from app.services.schemas import SessionData, Pair, TestData, QuestionData, AssessmentReport
from app.services.report_service import FinalReportService
from core_logic.Assessment.test_inference import get_inference
from app.services.security_service import EncryptionService
from core_logic.Accessories.logger import logging
from core_logic.Data.database import TestHistory
from copy import deepcopy
import json
import os 


class AssessmentService:
    def __init__(self, knowledge_base: dict, test_data: dict, abbr_map: dict,report_service: FinalReportService,db_session, encryption_service: EncryptionService):
        self.knowledge_base = knowledge_base
        self.test_data = test_data
        self.abbr_map = abbr_map
        self.report_service = report_service
        self.db = db_session
        self.encryption_service = encryption_service

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
        

        # Use the test name (not disorder name) to get abbreviation
        abbreviation = self.abbr_map.get(test_name) if test_name else None

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
        logging.info(f"[AssessmentService] Mapped to test: {test_name} (abbreviation: {abbreviation})")
        
        logging.info(f"[AssessmentService] Formatted answers for inference: {answers}")
        
        # Get the score and interpretation
        raw_score, score_interpretation = get_inference(test_name, answers)
        logging.info(f"[AssessmentService] Calculated raw score: {raw_score}, interpretation: {score_interpretation}")

        # Create the assessment report
        session_data.assessment_data = AssessmentReport(
            test_name=test_name if test_name else "Assessment", 
            answers=answers, 
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
    


    def save_assessment_history(self, username: str, final_assessment_result: SessionData) -> bool:
            """
            Encrypts sensitive fields within the session data and saves the complete
            assessment history to the database as a JSONB object.
            """
            logging.info(f"[AssessmentService] Preparing to save encrypted history for user: {username}")
            try:
                # --- THE NEW ENCRYPTION LOGIC ---

                # 1. Create a deep copy of the result object to avoid side effects.
                # We don't want to encrypt the object that's being sent back to the user's UI.
                data_to_save = deepcopy(final_assessment_result)

                # 2. Identify and encrypt the sensitive fields WITHIN the object.
                # a) Encrypt the conversation history
                encrypted_history = []
                for turn in data_to_save.conversation_history:
                    encrypted_content = self.encryption_service.encrypt_data(turn.content)
                    encrypted_history.append({"role": turn.role, "content": encrypted_content})
                data_to_save.conversation_history = encrypted_history

                # b) Encrypt the final narrative report
                encrypted_report_str = ""
                if data_to_save.assessment_data and data_to_save.assessment_data.narrative_report:
                    report_string = data_to_save.assessment_data.narrative_report.model_dump_json()
                    encrypted_report_str = self.encryption_service.encrypt_data(report_string)
                    # Replace the original report object with the encrypted string
                    data_to_save.assessment_data.narrative_report = encrypted_report_str
                
                # 3. Convert the entire modified Pydantic object to a dictionary.
                # This dictionary is now a valid JSON structure.
                session_data_dict = data_to_save.model_dump()
                session_data_json_string = json.dumps(session_data_dict)

                # 4. Create the new database record using the corrected data types.
                new_history_entry = TestHistory(
                    user_name=username,
                    # Pass the dictionary directly to the JSONB column
                    encrypted_session_data=session_data_json_string,
                    # Pass the separately encrypted report string to the Text column
                    encrypted_final_report=encrypted_report_str
                )
                
                # 5. Add to session and commit
                self.db.add(new_history_entry)
                self.db.commit()
                
                logging.info(f"Successfully saved encrypted history for user {username}")
                return True

            except Exception as e:
                self.db.rollback()
                logging.error(f"Failed to save encrypted history for user {username}: {str(e)}")
                return False

