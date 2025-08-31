import uuid
from fastapi import APIRouter, Depends, HTTPException
from app.services.schemas import StartRequest, StartResponse, SessionData, ConversationTurn
from app.services.conversation_service import ConversationService
from app.privacy.redaction import redact_pii
from app.safety.checker import check_for_crisis
from core_logic.Accessories.exception import CustomException
from core_logic.Accessories.logger import logging

# --- Dependency Injection (will be wired in main.py) ---
def get_conversation_service() -> ConversationService:
    # This is a placeholder that will be overridden in main.py
    raise NotImplementedError("get_conversation_service dependency not implemented")

router = APIRouter()

@router.post("/start", response_model=StartResponse, summary="Start a new conversation")
def start_conversation(
    request: StartRequest,
    convo_service: ConversationService = Depends(get_conversation_service)
):
    """
    Initiates a new conversation by performing safety checks, creating a state object,
    and generating the first AI probing question.
    """
    # --- 1. Consent Check (Implicit in the request model) ---
    # In a real app, you might also log this consent action.
    if not request.consent_given:
        raise HTTPException(status_code=400, detail="Consent is required to start.")

    # --- 2. Security & Privacy Layer ---
    cleaned_text = redact_pii(request.initial_text)
    if check_for_crisis(cleaned_text):
        # In a real app, you would log this event for review
        raise HTTPException(
            status_code=422, 
            detail="High-risk content detected. Please seek immediate help."
        )

    logging.info(f"Redacted User Input: {cleaned_text}")
    # --- 3. Generate the Probing Question ---
    probing_question = convo_service.generate_probing_question(cleaned_text)
    logging.info("Probing Question Generated: ", probing_question)

    # --- 4. Create the Initial SessionData State Object ---
    session_id = str(uuid.uuid4())
    initial_state = SessionData(
        session_id=session_id,
        status="priming",
        ai_question_to_ask_user=probing_question,
        conversation_history=[
            ConversationTurn(role="user", content=cleaned_text),
            ConversationTurn(role="assistant", content=probing_question)
        ],
        # The rest of the state is empty for now
        belief_state=None,
        final_category=None,
        assessment_data=None
    )

    # --- 5. Return the Response ---
    # The UI now has everything it needs: the question to ask and the state to hold.
    return StartResponse(
        ai_question=probing_question,
        session_data=initial_state
    )