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
                
                # Add debugging
                logging.info(f"[UI] Assessment ready for category: {session_data.final_category}")
                logging.info(f"[UI] Session status: {session_data.status}")
                
                # Get assessment service dependency
                try:
                    assessment_service: AssessmentService = get_assessment_service()
                    test_data = assessment_service.get_assessment_for_category(session_data.final_category)
                    logging.info(f"[UI] Successfully got test data: {test_data.test_name}")
                    
                    # Create assessment form HTML
                    assessment_template = templates.get_template("partials/assessment_workspace.html")
                    assessment_html = assessment_template.render({
                        "request": request,
                        "session_data": session_data.model_dump(),
                        "test_data": test_data.model_dump()
                    })
                    
                    # Create updated chat view HTML
                    chat_template = templates.get_template("partials/chat_interface.html")
                    chat_html = chat_template.render({
                        "request": request,
                        "session_data": session_data.model_dump()
                    })
                    
                    # Return both updates using HTMX OOB
                    return HTMLResponse(
                        f'<div hx-swap-oob="innerHTML:#content-workspace">{assessment_html}</div>'
                        f'<div hx-swap-oob="innerHTML:#chat-container">{chat_html}</div>'
                    )
                    
                except Exception as e:
                    logging.error(f"[UI] Error getting assessment: {str(e)}")
                    # Return an error message instead of crashing
                    error_html = f'''
                    <div class="p-4 bg-red-50 border border-red-200 rounded-lg">
                        <h3 class="text-red-800">Assessment Loading Error</h3>
                        <p class="text-red-700">Sorry, we couldn't load the assessment for "{session_data.final_category}". Please try again.</p>
                        <p class="text-sm text-red-600 mt-2">Error: {str(e)}</p>
                    </div>
                    '''
                    return HTMLResponse(
                        f'<div hx-swap-oob="innerHTML:#content-workspace">{error_html}</div>'
                    )
            else:
                # Continuing conversation
                updated_state = respond_result.session_data

        # Regular conversation continues - re-render chat view
        return templates.TemplateResponse("partials/chat_interface.html", {
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
        return templates.TemplateResponse("partials/chat_interface.html", {
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
            
            return templates.TemplateResponse("partials/results_workspace.html", {
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



# --- Endpoint 4: Main Assessment Interface ---
@router.get("/hi", response_class=HTMLResponse)
async def get_assessment_interface(request: Request):
    """Serves the main assessment interface with split-screen layout"""
    logging.info("[UI] GET /hi called - serving main assessment interface")
    return templates.TemplateResponse("assessment_interface.html", {"request": request})

# --- Endpoint 5: Serve the welcome view ---
@router.get("/welcome_view", response_class=HTMLResponse)
async def get_welcome_view(request: Request):
    """Serves the initial welcome content"""
    logging.info("[UI] GET /welcome_view called")
    return templates.TemplateResponse("partials/workspace_welcome.html", {"request": request})

# ============================================================================
# TEST ENDPOINTS - Remove these in production
# ============================================================================

@router.get("/test_assessment/{category}", response_class=HTMLResponse)
async def test_assessment_form(
    request: Request,
    category: str,
    assessment_service: AssessmentService = Depends(get_assessment_service)
):
    """Test endpoint to directly render assessment form for any category"""
    logging.info(f"[TEST] Testing assessment form for category: {category}")
    
    try:
        # Get test data
        test_data = assessment_service.get_assessment_for_category(category)
        
        # Create mock session data
        mock_session_data = {
            "session_id": "test-session-direct",
            "status": "assessing", 
            "final_category": category,
            "conversation_history": [
                {"role": "user", "content": "I've been struggling with mental health issues"},
                {"role": "assistant", "content": "I understand. Let's proceed with an assessment."}
            ],
            "belief_state": {category: 1.0},
            "assessment_data": None
        }
        
        # Create a complete HTML page for testing
        form_content = templates.get_template("partials/assessment_form.html").render({
            "request": request,
            "session_data": mock_session_data,
            "test_data": test_data.model_dump()
        })
        
        test_html = f'''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Test - {test_data.test_name}</title>
            <link href="/static/css/output.css" rel="stylesheet">
            <script src="https://unpkg.com/htmx.org@1.9.10" defer></script>
            <style>
                .htmx-indicator {{
                    display: none;
                }}
                .htmx-request .htmx-indicator {{
                    display: block;
                }}
                .htmx-request button {{
                    opacity: 0.6;
                    pointer-events: none;
                }}
            </style>
        </head>
        <body class="bg-gray-100 min-h-screen">
            <div class="max-w-4xl mx-auto py-8 px-4">
                <div class="bg-white rounded-lg shadow-lg p-6">
                    <div class="mb-6">
                        <h1 class="text-3xl font-bold text-gray-900">Testing Mode</h1>
                        <p class="text-gray-600">Category: {category.replace('_', ' ')}</p>
                        <a href="/ui/test_dashboard" class="text-blue-600 hover:text-blue-800">← Back to Test Dashboard</a>
                    </div>
                    <div id="content-area">
                        {form_content}
                    </div>
                </div>
            </div>
        </body>
        </html>
        '''
        
        return HTMLResponse(test_html)
        
    except Exception as e:
        logging.error(f"[TEST] Error in test assessment: {str(e)}")
        error_html = f'''
        <div class="p-4 bg-red-50 border border-red-200 rounded-lg">
            <h3 class="text-red-800">Test Error</h3>
            <p class="text-red-700">Error testing category "{category}": {str(e)}</p>
            <details class="mt-2">
                <summary class="text-sm text-red-600 cursor-pointer">Error Details</summary>
                <pre class="text-xs text-red-500 mt-1">{str(e)}</pre>
            </details>
        </div>
        '''
        return HTMLResponse(error_html)

@router.get("/test_dashboard", response_class=HTMLResponse)
async def get_test_dashboard(request: Request):
    """Serve the testing dashboard with complete HTML page"""
    categories = [
        ("Generalized_Anxiety_Disorder", "Generalized Anxiety Disorder"),
        ("Social_Anxiety_Disorder", "Social Anxiety Disorder"), 
        ("Major_Depressive_Disorder", "Major Depressive Disorder"),
        ("Bipolar_Disorder", "Bipolar Disorder"),
        ("Post_Traumatic_Stress_Disorder", "PTSD"),
        ("Obsessive_Compulsive_Disorder", "OCD"),
        ("Borderline_Personality_Disorder", "Borderline Personality Disorder")
    ]
    
    dashboard_html = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Miraat Assessment Testing Dashboard</title>
        <link href="/static/css/output.css" rel="stylesheet">
        <script src="https://unpkg.com/htmx.org@1.9.10" defer></script>
    </head>
    <body class="bg-gray-100 min-h-screen">
        <div class="max-w-6xl mx-auto py-8 px-4">
            <div class="bg-white rounded-lg shadow-lg p-6">
                <div class="mb-6">
                    <h1 class="text-3xl font-bold text-gray-900">🧪 Assessment Testing Dashboard</h1>
                    <p class="text-gray-600 mt-2">Test individual assessment forms without going through the conversation flow.</p>
                </div>
                
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    '''
    
    for category_key, category_name in categories:
        dashboard_html += f'''
                    <div class="border border-gray-200 p-4 rounded-lg hover:border-blue-300 hover:shadow-md transition-all">
                        <h3 class="font-semibold text-lg text-gray-800 mb-2">{category_name}</h3>
                        <p class="text-sm text-gray-600 mb-3">Test the assessment form for this category</p>
                        <div class="flex flex-col space-y-2">
                            <a href="/ui/test_assessment/{category_key}" 
                               class="inline-block px-4 py-2 bg-blue-500 text-white rounded text-sm text-center hover:bg-blue-600 transition-colors">
                               📝 Test Assessment Form
                            </a>
                        </div>
                    </div>
        '''
    
    dashboard_html += '''
                </div>
                
                <div class="mt-8 p-6 bg-blue-50 border border-blue-200 rounded-lg">
                    <h4 class="font-semibold text-blue-800 text-lg mb-3">🚀 Usage Instructions</h4>
                    <ul class="text-blue-700 space-y-2">
                        <li class="flex items-start">
                            <span class="text-blue-500 mr-2">•</span>
                            <span>Click "Test Assessment Form" to see the complete rendered form for each mental health category</span>
                        </li>
                        <li class="flex items-start">
                            <span class="text-blue-500 mr-2">•</span>
                            <span>Forms are fully functional - you can fill them out and submit to test the complete flow</span>
                        </li>
                        <li class="flex items-start">
                            <span class="text-blue-500 mr-2">•</span>
                            <span>No conversation setup required - jump straight to testing specific assessments</span>
                        </li>
                        <li class="flex items-start">
                            <span class="text-blue-500 mr-2">•</span>
                            <span><strong>Remember:</strong> Remove these test endpoints before production deployment!</span>
                        </li>
                    </ul>
                </div>
                
                <div class="mt-6 text-center">
                    <a href="/" class="text-blue-600 hover:text-blue-800 underline">← Back to Main App</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''
    
    return HTMLResponse(dashboard_html)