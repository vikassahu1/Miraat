# app/services/report_service.py
from app.services.conversation_service import ConversationService # We might reuse the LLM client
from app.schemas import SessionData

class FinalReportService:
    def __init__(self, convo_service: ConversationService):
        # We can reuse the LLM client from the ConversationService
        self.llm_client = convo_service.llm_client 

    def generate_final_summary(self, session_data: SessionData) -> str:
        """
        Generates a high-quality, context-aware, and safe narrative summary
        of the user's entire session.
        """
        if not self.llm_client:
            return "Could not generate a summary at this time."

        # --- 1. Assemble the Full Context ---
        # This is the most important step. We gather all the evidence.
        
        # The user's own words
        conversation_transcript = "\n".join(
            f"{turn['role']}: {turn['content']}" for turn in session_data.conversation_history
        )
        
        # The factual, clinical findings
        assessment_report = session_data.assessment_data
        test_name = assessment_report.test_name
        final_score = assessment_report.final_score
        interpretation = assessment_report.interpretation

        # TODO: Make this part better.
        # --- 2. Professional, Multi-Part Prompt Engineering ---
        system_prompt = (
            "You are an expert AI assistant specializing in mental health communication. "
            "Your task is to synthesize a user's conversation and assessment results into a single, supportive, and actionable summary. "
            "RULES: "
            "1. **DO NOT DIAGNOSE.** Never use phrases like 'you have' or 'you are suffering from'. Instead, use 'your results suggest' or 'it appears you are experiencing symptoms of'. "
            "2. **BE EMPATHETIC AND VALIDATING.** Start by acknowledging the user's feelings shown in the conversation. "
            "3. **BE FACTUAL.** Clearly state the name of the assessment and the interpretation of the score. "
            "4. **BE ACTIONABLE.** Provide 2-3 general, safe, and encouraging next steps. Focus on self-care, seeking professional help, and psychoeducation. "
            "5. **INCLUDE A CLEAR DISCLAIMER.** End with a statement that this is not a substitute for professional medical advice. "
            "6. **BE CONCISE.** Keep the entire summary to 3-4 short paragraphs."
        )

        user_prompt = (
            f"Please generate a final summary based on the following information:\n\n"
            f"---CONVERSATION TRANSCRIPT---\n{conversation_transcript}\n\n"
            f"---ASSESSMENT RESULTS---\n"
            f"Test Taken: {test_name}\n"
            f"Final Score: {final_score}\n"
            f"Clinical Interpretation: {interpretation}\n\n"
            f"---YOUR SUMMARY---"
        )

        # --- 3. The LLM Call ---
        try:
            # We can reuse the _make_llm_call from ConversationService if we make it public
            # For now, let's write it out for clarity
            chat_completion = self.llm_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                model="llama3-8b-8192", # Or a more powerful model like llama3-70b for the final summary
                temperature=0.7,
            )
            summary = chat_completion.choices[0].message.content
            return summary.strip()

        except Exception as e:
            print(f"Final summary generation failed: {e}")
            # A safe, generic fallback
            return f"Based on your assessment, the results indicate '{interpretation}'. Seeking guidance from a healthcare professional can provide further clarity and support."