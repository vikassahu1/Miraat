from core_logic.LLM.llm_endpoint import llm
from core_logic.Accessories.exception import CustomException
from core_logic.Accessories.logger import logging
from core_logic.Accessories.exception import CustomException
from core_logic.Accessories.logger import logging


class ConversationService:
    def __init__(self, knowledge_base: dict):
        self.knowledge_base = knowledge_base
        try:
            self.llm_client = llm
            logging.info("ConversationService: Gemini LLM client initialized.")
        except Exception:
            self.llm_client = None
            logging.info("ConversationService: Could not initialize Gemini LLM client.")

    def _make_llm_call(self, system_prompt: str, user_prompt: str) -> str:
        if not self.llm_client:
            return "Error: LLM not available."
        try:
            # Compose the prompt for Gemini
            prompt = f"{system_prompt}\n\n{user_prompt}"
            response = self.llm_client.invoke(prompt)
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            print(f"LLM call failed: {e}")
            return "Error: LLM call failed."


    # --- NEW FUNCTION FOR THE PRIMING STAGE ---
    def generate_probing_question(self, initial_text: str) -> str:
        """
        Generates a simple, open-ended question to encourage the user to elaborate.
        This is the first step in the priming conversation.
        """
        system_prompt = (
            "You are an empathetic AI assistant. A user has just shared their initial feeling. "
            "Your ONLY job is to ask one simple, open-ended question to encourage them to elaborate on the IMPACT this feeling is having on their daily life. "
            "Do not give advice. Do not analyze. "
            "Ask the question directly, but make it warm, and empathetic. "
            "NOTE: Some words in the text will appear in square brackets like [this]; these are placeholders for sensitive information that has been redacted for privacy. Do not ask about or reference these placeholders."
            "VERY CRITICAL:Also even if by accidently the text contains PII information like Names, Phone numbers, Emails, Credit Card numbers etc, do not ask about or reference these details. NEVER USE THESE INFO IN REPLY ANYHOW (Person Names, Phone numbers, Emails, Credit Card numbers)"
        )
        user_prompt = f"User's initial feeling: \"{initial_text}\"\n\nGenerate the probing question:"
        
        fallback_question = "Thank you for sharing. Could you tell me a bit more about how this has been affecting your day-to-day life?"
        
        try:
            question = self._make_llm_call(system_prompt, user_prompt)
            logging.info(f"LLM generated probing question: {question}")
            # Basic cleanup of the LLM output
            return question.strip().strip('"') if question and "Error" not in question else fallback_question
        except Exception:
            return fallback_question

    # ... (The other functions like generate_differentiating_question will be used in the next stage) ...