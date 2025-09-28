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
def get_convo_service() -> ConversationService: 
    # This will be overridden by main.py
    raise NotImplementedError("Service dependency not properly injected")

def get_triage_service() -> TriageService: 
    # This will be overridden by main.py
    raise NotImplementedError("Service dependency not properly injected")

def get_assessment_service() -> AssessmentService: 
    # This will be overridden by main.py
    raise NotImplementedError("Service dependency not properly injected")

def get_report_service() -> FinalReportService: 
    # This will be overridden by main.py
    raise NotImplementedError("Service dependency not properly injected")

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# --- Endpoint 1: Renders the initial chat box ---
@router.get("/initial_chat_view", response_class=HTMLResponse)
async def get_initial_chat_view(request: Request):
    """This renders the chat_view when the session_data is None"""
    logging.info("[UI] GET /initial_chat_view called")
    return templates.TemplateResponse("partials/chat_interface.html", {
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
    triage_service: TriageService = Depends(get_triage_service),
    assessment_service: AssessmentService = Depends(get_assessment_service)
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
                logging.info("[UI] Conversation indicates assessment is ready")
                session_data = respond_result.session_data
                
                # Add debugging
                logging.info(f"[UI] Assessment ready for category: {session_data.final_category}")
                logging.info(f"[UI] Session status: {session_data.status}")
                
                # Use the injected assessment service instead of calling get_assessment_service()
                try:
                    test_data = assessment_service.get_assessment_for_category(session_data.final_category)
                    logging.info(f"[UI] Successfully got test data: {test_data.test_name}")
                    logging.info(f"[UI] Complete test data: {test_data}")
                    
                    # Create assessment form HTML - return directly for HTMX target replacement
                    return templates.TemplateResponse("partials/assessment_workspace.html", {
                        "request": request,
                        "session_data": session_data.model_dump(),
                        "test_data": test_data.model_dump()
                    })
                    
                    
                except Exception as e:
                    logging.error(f"[UI] Error getting assessment data: {str(e)}")
                    error_html = f'<div class="p-4 text-red-600">Assessment Loading Error: {str(e)}</div>'
                    return HTMLResponse(error_html)
            
            else:
                # Continue conversation normally
                updated_state = respond_result.session_data
                
        # Render regular chat interface for ongoing conversation
        return templates.TemplateResponse("partials/chat_interface.html", {
            "request": request,
            "session_data": updated_state.model_dump()
        })
        
    except Exception as e:
        logging.error(f"[UI] Error in conversation_turn: {str(e)}")
        # For debugging, let's show the actual error
        error_message = f"Error: {str(e)}"
        return templates.TemplateResponse("partials/chat_interface.html", {
            "request": request,
            "session_data": None,
            "error_message": error_message
        })

# --- Endpoint 3: Handle workspace loading (for welcome screen) ---
@router.get("/workspace_welcome", response_class=HTMLResponse)
async def get_workspace_welcome(request: Request):
    """Renders the welcome workspace"""
    logging.info("[UI] GET /workspace_welcome called")
    return templates.TemplateResponse("partials/workspace_welcome.html", {
        "request": request
    })

# --- Endpoint 4: Assessment form submission ---
@router.post("/submit_assessment", response_class=HTMLResponse)
async def submit_assessment_endpoint(
    request: Request,
    session_data_json: str = Form(...),
    assessment_service: AssessmentService = Depends(get_assessment_service),
    report_service: FinalReportService = Depends(get_report_service)
):
    """
    Handles submission of assessment answers and generates final report
    """
    logging.info("[UI] POST /submit_assessment called")
    
    try:
        # Parse session data
        session_data = SessionData(**json.loads(session_data_json))
        
        # Collect all answers from the form
        form_data = await request.form()
        assessment_answers = {}
        
        for key, value in form_data.items():
            if key.startswith('answer_'):
                question_id = key.replace('answer_', '')
                assessment_answers[question_id] = value
        
        logging.info(f"[UI] Collected {len(assessment_answers)} assessment answers")
        
        # Create assessment request
        assessment_request = AssessmentSubmitRequest(
            session_data=session_data,
            answers=assessment_answers
        )
        
        # Process assessment
        assessment_result = submit_assessment_logic(
            assessment_request, 
            assessment_service, 
        )
        
        logging.info(f"[UI] Assessment processing completed with status: {assessment_result.status}")
        logging.info(f"[UI] Generating final report: {assessment_result.assessment_data.narrative_report}")
        
        # Return results view directly for HTMX target replacement
        return templates.TemplateResponse("partials/results_workspace.html", {
            "request": request,
            "session_data": assessment_result.model_dump(),
            "final_report": assessment_result.assessment_data.narrative_report.model_dump() if assessment_result.assessment_data and assessment_result.assessment_data.narrative_report else None
        })
        
    except Exception as e:
        logging.error(f"[UI] Error in submit_assessment: {str(e)}")
        error_html = f'<div class="p-4 text-red-600">Assessment Submission Error: {str(e)}</div>'
        return HTMLResponse(error_html)


# --- Endpoint 5: Load main assessment interface ---
@router.get("/", response_class=HTMLResponse)
async def get_assessment_interface(request: Request):
    """Main endpoint to load the assessment interface"""
    logging.info("[UI] GET / called")
    return templates.TemplateResponse("assess.html", {
        "request": request
    })
