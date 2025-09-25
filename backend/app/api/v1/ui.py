# app/api/v1/ui.py
import json
from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional, Dict, Any

# Import your schemas and ALL your services
from app.services.schemas import SessionData, ConversationTurn, StartRequest, RespondRequest, AssessmentSubmitRequest
from app.services.conversation_service import ConversationService
from app.services.triage_service import TriageService
from app.services.assessment_service import AssessmentService
from app.services.report_service import FinalReportService

from app.logic.conversation import start_conversation as start_conversation_logic, respond_conversation as respond_conversation_logic
from app.logic.assessment import submit_assessment as submit_assessment_logic
from core_logic.Accessories.logger import logging
from core_logic.Accessories.exception import CustomException
import sys

# --- Dependency Injection Setup ---
def get_convo_service() -> ConversationService: raise NotImplementedError
def get_triage_service() -> TriageService: raise NotImplementedError
def get_assessment_service() -> AssessmentService: raise NotImplementedError
def get_report_service() -> FinalReportService: raise NotImplementedError

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# --- Endpoint 1: Renders the initial chat box ---
@router.get("/initial_chat_view", response_class=HTMLResponse)
async def get_initial_chat_view(request: Request):
    """This renders the chat_view when the session_data is None"""
    logging.info("[UI] GET /initial_chat_view called")
    initial_history = [{"role": "assistant", "content": "Hello! Please share what's on your mind."}]
    return templates.TemplateResponse("partials/chat_view.html", {
        "request": request,
        "session_data": None  # This triggers the initial form rendering
    })

# --- Endpoint 2: The main conversation endpoint ---
@router.post("/conversation_turn", response_class=HTMLResponse)
async def handle_conversation_turn(
    request: Request,
    user_input: str = Form(...),
    session_data_json: Optional[str] = Form(None),
    convo_service: ConversationService = Depends(get_convo_service),
    triage_service: TriageService = Depends(get_triage_service)
):
    """
    This single endpoint handles BOTH starting a conversation AND continuing it.
    """
    logging.info(f"[UI] POST /conversation_turn called with input: {user_input[:50]}...")
    
    try:
        if session_data_json is None:
            # --- THIS IS THE FIRST TURN ---
            logging.info("[UI] First turn - starting new conversation")
            start_request = StartRequest(initial_text=user_input, consent_given=True)
            start_response = start_conversation_logic(start_request, convo_service)
            updated_state = start_response.session_data
            
        else:
            # --- THIS IS A SUBSEQUENT TURN ---
            logging.info("[UI] Subsequent turn - continuing conversation")
            current_state = SessionData(**json.loads(session_data_json))
            respond_request = RespondRequest(user_answer=user_input, session_data=current_state)
            respond_result = respond_conversation_logic(respond_request, convo_service, triage_service)
            
            # Handle RespondResponse object
            if respond_result.status == "assessment_ready":
                # Time to show assessment form
                session_data = respond_result.session_data
                
                # Get assessment service dependency
                assessment_service: AssessmentService = get_assessment_service()
                test_data = assessment_service.get_assessment_for_category(session_data.final_category)
                
                # Create assessment form HTML
                assessment_template = templates.get_template("partials/assessment_form.html")
                assessment_html = assessment_template.render({
                    "request": request,
                    "session_data": session_data.model_dump(),
                    "test_data": test_data.model_dump()
                })
                
                # Create updated chat view HTML
                chat_template = templates.get_template("partials/chat_view.html")
                chat_html = chat_template.render({
                    "request": request,
                    "session_data": session_data.model_dump()
                })
                
                # Return both updates using HTMX OOB
                return HTMLResponse(
                    f'<div hx-swap-oob="innerHTML:#content-workspace">{assessment_html}</div>'
                    f'<div hx-swap-oob="innerHTML:#chat-container">{chat_html}</div>'
                )
            else:
                # Continuing conversation
                updated_state = respond_result.session_data

        # Regular conversation continues - re-render chat view
        return templates.TemplateResponse("partials/chat_view.html", {
            "request": request,
            "session_data": updated_state.model_dump()
        })
        
    except Exception as e:
        logging.error(f"[UI] Error in conversation_turn: {str(e)}")
        error_message = f"Sorry, there was an error processing your request: {str(e)}"
        error_state = {
            "conversation_history": [
                {"role": "assistant", "content": error_message}
            ]
        }
        return templates.TemplateResponse("partials/chat_view.html", {
            "request": request,
            "session_data": error_state
        })


# --- Endpoint 3: Handles the submission of the final assessment ---
@router.post("/submit_assessment", response_class=HTMLResponse)
async def submit_assessment_ui(
    request: Request,
    session_data_json: str = Form(...),
    assessment_service: AssessmentService = Depends(get_assessment_service)
):
    """Handle assessment submission and generate final report"""
    logging.info("[UI] POST /submit_assessment called")
    
    try:
        # Parse session data
        session_data = SessionData(**json.loads(session_data_json))
        
        # Extract all form data to get answers
        form_data = await request.form()
        answers = {}
        
        # Process form data to extract answers
        for key, value in form_data.items():
            if key not in ['session_data_json']:  # Skip non-answer fields
                try:
                    answers[key] = int(value)
                except (ValueError, TypeError):
                    answers[key] = value
        
        logging.info(f"[UI] Extracted answers: {answers}")
        
        # Create assessment request
        submit_request = AssessmentSubmitRequest(
            session_data=session_data,
            answers=answers
        )
        
        # Call logic layer to process assessment
        completed_session_data = submit_assessment_logic(submit_request, assessment_service)
        
        # Extract the final report
        if completed_session_data.assessment_data and completed_session_data.assessment_data.narrative_report:
            report = completed_session_data.assessment_data.narrative_report
            
            return templates.TemplateResponse("partials/final_report.html", {
                "request": request,
                "report": report.model_dump()
            })
        else:
            raise HTTPException(status_code=500, detail="Failed to generate assessment report")
            
    except Exception as e:
        logging.error(f"[UI] Error in submit_assessment: {str(e)}")
        error_html = f'''
        <div class="p-4 bg-red-50 border border-red-200 rounded-lg">
            <h3 class="text-red-800">Assessment Error</h3>
            <p class="text-red-700">Sorry, there was an error processing your assessment: {str(e)}</p>
        </div>
        '''
        return HTMLResponse(error_html)



# --- Endpoint 4: Serve the welcome view ---
@router.get("/welcome_view", response_class=HTMLResponse)
async def get_welcome_view(request: Request):
    """Serves the initial welcome content"""
    logging.info("[UI] GET /welcome_view called")
    return templates.TemplateResponse("partials/welcome_content.html", {"request": request})