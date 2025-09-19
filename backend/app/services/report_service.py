from app.services.schemas import SessionData, FinalReport, ConversationTurn, AssessmentReport
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from core_logic.Accessories.logger import logging
from core_logic.LLM.llm_endpoint import llm
import os


class FinalReportService:
    def __init__(self):
        try:
            self.llm = llm
            self.parser = StrOutputParser() 
            logging.info("FinalReportService: LangChain initialized for report generation.")
        except Exception as e:
            self.llm = None
            print(f"FATAL: Could not initialize FinalReportService. Error: {e}")

    # --- Single, Focused LLM Call ---
    def _generate_section(self, prompt_template: ChatPromptTemplate, context: dict) -> str:
        if not self.llm:
            return "Content could not be generated at this time."
        try:
            chain = prompt_template | self.llm | self.parser
            return chain.invoke(context)
        except Exception as e:
            print(f"Failed to generate report section: {e}")
            return f"Error generating content for this section."

    # --- Private Method for Section 1: The Opening ---
    def _generate_opening(self, transcript: str) -> str:
        prompt = ChatPromptTemplate.from_template(
            "You are an empathetic AI psychologist. Your task is to write a warm, validating opening paragraph for a user's assessment report. "
            "Directly reference specific feelings and challenges the user mentioned in the conversation transcript to make them feel heard. "
            "Do not analyze or give results, just provide an empathetic summary of their expressed feelings. Write at least 3-4 sentences.\n\n"
            "---CONVERSATION TRANSCRIPT---\n{transcript}\n\n"
            "---EMPATHETIC OPENING PARAGRAPH---"
        )
        return self._generate_section(prompt, {"transcript": transcript})

    # --- Private Method for Section 2: The Findings ---
    def _generate_findings(self, test_name: str, score: float, interpretation: str) -> str:
        prompt = ChatPromptTemplate.from_template(
            "You are a clinical assistant. Your task is to explain assessment results in a clear, factual, and non-alarming way. "
            "Write a paragraph of at least 3 sentences that includes the full test name, the numerical score, and what the clinical interpretation means in simple terms. "
            "Frame the result as a confirmation of the user's experience, not a label.\n\n"
            "---ASSESSMENT DATA---\nTest: {test_name}\nScore: {score}\nInterpretation: {interpretation}\n\n"
            "---FACTUAL FINDINGS PARAGRAPH---"
        )
        return self._generate_section(prompt, {"test_name": test_name, "score": score, "interpretation": interpretation})

    # --- Private Method for Section 3: The Next Steps ---
    def _generate_steps(self, transcript: str, interpretation: str) -> str:
        prompt = ChatPromptTemplate.from_template(
            "You are a helpful AI guide. Your task is to suggest 2-3 safe, general, and actionable next steps for a user. "
            "Write a paragraph beginning with 'Here are a few gentle suggestions...'. The steps should be relevant to the user's interpretation and the problems they mentioned in the transcript (e.g., if they mentioned sleep, suggest sleep hygiene). "
            "Use encouraging, non-commanding language. Write at least 3-4 sentences.\n\n"
            "---CONTEXT---\nInterpretation: {interpretation}\nTranscript Snippets: {transcript}\n\n"
            "---RECOMMENDED STEPS PARAGRAPH---"
        )
        return self._generate_section(prompt, {"interpretation": interpretation, "transcript": transcript})

    # --- The Main Public Method that Orchestrates the Chain ---
    def generate_final_report(self, session_data: SessionData) -> FinalReport:
        print("--- Starting Final Report Generation Chain ---")
        logging.info("Generating final report using LangChain...")
        
        # --- 1. Assemble Context (Same as before) ---
        transcript = "\n".join(f"{turn.role}: {turn.content}" for turn in session_data.conversation_history)
        report_data = session_data.assessment_data

        # --- 2. Run the Generation Chain, Step-by-Step ---
        print("Generating Section 1: Opening Summary...")
        logging.info("Generating opening summary for final report.")
        opening = self._generate_opening(transcript)
        
        print("Generating Section 2: Assessment Findings...")
        logging.info("Generating assessment findings for final report.")
        findings = self._generate_findings(report_data.test_name, report_data.final_score, report_data.interpretation)
        
        print("Generating Section 3: Recommended Steps...")
        logging.info("Generating recommended steps for final report.")
        steps = self._generate_steps(transcript, report_data.interpretation)
        
        print("--- Report Generation Complete ---")
        
        # --- 3. Assemble the Final, Simple Report Object ---
        return FinalReport(
            opening_summary=opening,
            assessment_findings=findings,
            recommended_steps=steps
            # The disclaimer will use the Pydantic default value
        )



if __name__ == '__main__':
    # --- 1. Load Environment Variables ---
    # We need to go up two directories from 'app/services' to find the root .env file
    # dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
    # load_dotenv(dotenv_path=dotenv_path)

    print("--- Running FinalReportService Test ---")

    # --- 2. Create Realistic Dummy SessionData ---
    # This simulates the state of the application right before the final report is generated.
    dummy_session_data = SessionData(
        session_id="test-session-123",
        status="assessing", # The status right before we call the service
        ai_question_to_ask_user=None,
        conversation_history=[
            ConversationTurn(role="user", content="I've been feeling so worried and stressed lately, I can't seem to relax."),
            ConversationTurn(role="assistant", content="That sounds really difficult. Can you tell me more about how this worry is affecting your daily life?"),
            ConversationTurn(role="user", content="It's hard to focus at work and I'm not sleeping well."),
            ConversationTurn(role="assistant", content="Is this a general feeling of worry about many different things, or is it often triggered by specific situations?"),
            ConversationTurn(role="user", content="It's pretty general, I worry about everything."),
        ],
        belief_state={"Generalized_Anxiety_Disorder": 0.98, "Mood Disorders": 0.02},
        final_category="Generalized_Anxiety_Disorder",
        assessment_data=AssessmentReport(
            test_name="Generalized Anxiety Disorder 7 (GAD-7)",
            answers={"q1": 3, "q2": 3, "q3": 2, "q4": 3, "q5": 2, "q6": 1, "q7": 2},
            final_score=16.0,
            interpretation="Moderately Severe Anxiety",
            narrative_report=None # This is what we want to generate
        )
    )

    # --- 3. Initialize and Run the Service ---
    # Create an instance of the service
    report_service = FinalReportService()

    if report_service.llm:
        print("\nGenerating final report...")
        # Call the function with our dummy data
        final_report = report_service.generate_final_report(dummy_session_data)

        # --- 4. Print the Structured Output ---
        print("\n--- ✅ Final Structured Report ---")
        # Use .model_dump_json for pretty printing
        print(final_report.model_dump_json(indent=2))
        print("---------------------------------")
    else:
        print("\n--- ❌ LLM Client failed to initialize. Could not run test. ---")