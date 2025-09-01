import uuid
from fastapi import APIRouter, Depends, HTTPException
from app.services.schemas import StartRequest, StartResponse, SessionData, ConversationTurn, RespondResponse, RespondRequest
from app.services.conversation_service import ConversationService
from app.services.triage_service import TriageService 
from app.privacy.redaction import redact_pii
from app.safety.checker import check_for_crisis
from core_logic.Accessories.exception import CustomException
from core_logic.Accessories.logger import logging

# Dependency Injection 
def get_conversation_service() -> ConversationService:
    # This is a placeholder that will be overridden in main.py
    raise NotImplementedError("get_conversation_service dependency not implemented")

def get_triage_service() -> TriageService:
    raise NotImplementedError("get_triage_service dependency not implemented")


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




@router.post("/respond", response_model=RespondResponse, summary="Continue the conversation")
def respond_conversation(
    request: RespondRequest,
    convo_service: ConversationService = Depends(get_conversation_service),
    triage_service: TriageService = Depends(get_triage_service) 
):
    current_state = request.session_data
    current_state.conversation_history.append(
        ConversationTurn(role="user", content=request.user_answer)
    )

    
    if current_state.status == "priming":
        # initial triage.
        user_text_full = " ".join(
            turn.content for turn in current_state.conversation_history if turn.role == 'user'
        )
        
        hypotheses = triage_service.get_initial_hypotheses(user_text_full)
        
        if not hypotheses:
            raise HTTPException(status_code=500, detail="Triage failed to produce hypotheses.")

        logging.info(f"Initial Hypotheses: {hypotheses}")
        
        # Updating State 
        current_state.status = "refining_broad"
        current_state.belief_state = {h['category']: h['score'] for h in hypotheses}
        
        updated_state = current_state
    
    elif current_state.status == "refining_broad":

        evaluation = convo_service.evaluate_user_answer(current_state.model_dump())
        updated_state = convo_service.update_belief_state(current_state, evaluation)


        logging.info(f"Updated Belief State: {updated_state.belief_state}")
        final_broad_category = convo_service.check_funnel_completion(updated_state)

        if final_broad_category:
            # Broad category found! Time to transition to subcategories.
            # subcategories = knowledge_base[final_broad_category]["Subcategories"]
            subcategories = convo_service.get_subcategories(final_broad_category)
            logging.info(f"Subcategories for {final_broad_category}: {subcategories.keys()}")
            
            # TRANSITION THE STATE
            updated_state.status = "refining_sub"
            updated_state.belief_state = {subcat: 1.0/len(subcategories) for subcat in subcategories.keys()}


    elif current_state.status == "refining_sub":
        # Evaluate the answer against the subcategories
        evaluation = convo_service.evaluate_user_answer(current_state)
        updated_state = convo_service.update_belief_state(current_state, evaluation)

        final_subcategory = convo_service.check_funnel_completion(updated_state)

        if final_subcategory:
            # Subcategory found! 
            # TRANSITION THE STATE
            updated_state.status = "assessing"
            updated_state.final_category = final_subcategory
            return {"status": "assessment_ready", "session_data": updated_state}
        
    

    next_question = convo_service.generate_differentiating_question(updated_state)
    updated_state.ai_question_to_ask_user = next_question
    updated_state.conversation_history.append(
        ConversationTurn(role="assistant", content=next_question)
    )
    
    return {"status": "in_progress", "ai_question": next_question, "session_data": updated_state}