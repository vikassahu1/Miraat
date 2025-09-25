import uuid
from fastapi import Depends, HTTPException, Form
from app.services.schemas import StartRequest, StartResponse, SessionData, ConversationTurn, RespondResponse, RespondRequest
from app.services.conversation_service import ConversationService
from app.services.assessment_service import AssessmentService
from app.services.triage_service import TriageService 
from app.privacy.redaction import redact_pii
from app.safety.checker import check_for_crisis
from core_logic.Accessories.exception import CustomException
from core_logic.Accessories.logger import logging
from fastapi import Request
from fastapi.responses import HTMLResponse
import json 


def start_conversation(
    request: StartRequest,
    convo_service: ConversationService
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
    logging.info(f"Probing Question Generated: {probing_question}")

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





def respond_conversation(
    request: RespondRequest,
    convo_service: ConversationService,
    triage_service: TriageService
):
    """
    Handle conversation responses and update session state
    """
    logging.info(f"[Logic] Received user response: {request.user_answer}")
    current_state = request.session_data
    
    # Add user response to conversation history
    current_state.conversation_history.append(
        ConversationTurn(role="user", content=request.user_answer)
    )

    if current_state.status == "priming":
        # Initial triage
        logging.info("[Logic] Performing initial triage, in phase priming.")

        user_text_full = " ".join(
            turn.content for turn in current_state.conversation_history if turn.role == 'user'
        )
        
        hypotheses = triage_service.get_initial_hypotheses(user_text_full)
        
        if not hypotheses:
            raise HTTPException(status_code=500, detail="Triage failed to produce hypotheses.")

        logging.info(f"[Logic] Initial Hypotheses: {hypotheses}")

        # Normalization of scores 
        raw_scores = {h['category']: h['score'] for h in hypotheses}
        total_score = sum(raw_scores.values())

        normalized_belief_state = {}
        if total_score > 0:
            # Divide each score by the total sum to get a probability
            normalized_belief_state = {
                category: score / total_score 
                for category, score in raw_scores.items()
            }
       
        logging.info(f"[Logic] Normalized Belief State: {normalized_belief_state}")

        # Update State 
        current_state.status = "refining_broad"
        current_state.belief_state = normalized_belief_state
        
    elif current_state.status == "refining_broad":
        logging.info("[Logic] Evaluating broad categories and updating the belief state.")
        evaluation = convo_service.evaluate_user_answer(current_state.model_dump())
        updated_state_dict = convo_service.update_belief_state(current_state.model_dump(), evaluation)
        
        # Update current_state with new belief state
        current_state.belief_state = updated_state_dict.get('belief_state', current_state.belief_state)
        
        logging.info(f"[Logic] Updated Belief State: {current_state.belief_state}")
        
        final_broad_category = convo_service.check_funnel_completion(current_state.model_dump())
        if final_broad_category:
            # Broad category found! Time to transition to subcategories.
            logging.info(f"[Logic] Final Broad Category Identified: {final_broad_category}")
            subcategories = convo_service._get_subcategories(final_broad_category)

            logging.info(f"[Logic] Subcategories for {final_broad_category}: {subcategories}")
            
            # TRANSITION THE STATE
            current_state.status = "refining_sub"
            current_state.belief_state = {subcat: 1.0/len(subcategories) for subcat in subcategories}

    elif current_state.status == "refining_sub":
        logging.info("[Logic] Refining subcategories.")
        evaluation = convo_service.evaluate_user_answer(current_state.model_dump())
        updated_state_dict = convo_service.update_belief_state(current_state.model_dump(), evaluation)
        
        # Update current_state with new belief state
        current_state.belief_state = updated_state_dict.get('belief_state', current_state.belief_state)
        
        logging.info(f"[Logic] Updated Belief State: {current_state.belief_state}")
        
        final_subcategory = convo_service.check_funnel_completion(current_state.model_dump())
        if final_subcategory:
            # Subcategory found! 
            # TRANSITION THE STATE
            current_state.status = "assessing"
            current_state.final_category = final_subcategory
            logging.info(f"[Logic] Final subcategory identified: {final_subcategory}. Ready for assessment.")
            return RespondResponse(
                status="assessment_ready", 
                ai_question=None,
                session_data=current_state
            )

    # Generate next question if still in conversation
    logging.info(f"[Logic] Current Status: {current_state.status}")
    next_question = convo_service.generate_differentiating_question(current_state.model_dump())
    current_state.ai_question_to_ask_user = next_question
    current_state.conversation_history.append(
        ConversationTurn(role="assistant", content=next_question)
    )
    
    return RespondResponse(
        status="in_progress", 
        ai_question=next_question, 
        session_data=current_state
    )




