# Add these test endpoints to your ui.py file for quick assessment testing
# Remove these in production

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
                {"role": "assistant", "content": "I understand. Let's proceed with an assessment to better understand your situation."}
            ],
            "belief_state": {category: 1.0},
            "assessment_data": None
        }
        
        return templates.TemplateResponse("partials/assessment_form.html", {
            "request": request,
            "session_data": mock_session_data,
            "test_data": test_data.model_dump()
        })
        
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

@router.get("/test_report/{category}", response_class=HTMLResponse)
async def test_final_report(
    request: Request,
    category: str,
    assessment_service: AssessmentService = Depends(get_assessment_service)
):
    """Test endpoint to directly render final report for any category"""
    logging.info(f"[TEST] Testing final report for category: {category}")
    
    try:
        from app.services.schemas import SessionData, ConversationTurn, AssessmentReport
        from app.logic.assessment import submit_assessment
        
        # Create mock completed session data
        mock_session_data = SessionData(
            session_id="test-report-session",
            status="assessing",
            final_category=category,
            conversation_history=[
                ConversationTurn(role="user", content="I've been struggling with anxiety and it's affecting my daily life"),
                ConversationTurn(role="assistant", content="Thank you for sharing. Let's complete this assessment.")
            ],
            belief_state={category: 1.0},
            assessment_data=None
        )
        
        # Create mock answers (simulating moderate severity)
        mock_answers = {}
        for i in range(1, 8):  # Assume 7 questions for most tests
            mock_answers[f"question_{i}"] = 2  # Moderate responses
        
        # Create assessment request
        from app.services.schemas import AssessmentSubmitRequest
        submit_request = AssessmentSubmitRequest(
            session_data=mock_session_data,
            answers=mock_answers
        )
        
        # Process assessment
        completed_session = submit_assessment(submit_request, assessment_service)
        
        if completed_session.assessment_data and completed_session.assessment_data.narrative_report:
            return templates.TemplateResponse("partials/final_report.html", {
                "request": request,
                "report": completed_session.assessment_data.narrative_report.model_dump()
            })
        else:
            raise Exception("Failed to generate report")
        
    except Exception as e:
        logging.error(f"[TEST] Error in test report: {str(e)}")
        error_html = f'''
        <div class="p-4 bg-red-50 border border-red-200 rounded-lg">
            <h3 class="text-red-800">Test Report Error</h3>
            <p class="text-red-700">Error testing report for "{category}": {str(e)}</p>
        </div>
        '''
        return HTMLResponse(error_html)

@router.get("/test_categories", response_class=HTMLResponse)
async def list_test_categories(request: Request):
    """List all available categories for testing"""
    categories = [
        "Generalized_Anxiety_Disorder",
        "Social_Anxiety_Disorder", 
        "Major_Depressive_Disorder",
        "Bipolar_Disorder",
        "Post_Traumatic_Stress_Disorder",
        "Obsessive_Compulsive_Disorder",
        "Borderline_Personality_Disorder"
    ]
    
    html = '''
    <div class="p-6 bg-white rounded-lg shadow">
        <h2 class="text-2xl font-bold mb-4">Assessment Testing Categories</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
    '''
    
    for category in categories:
        html += f'''
        <div class="border p-4 rounded-lg">
            <h3 class="font-semibold text-lg">{category.replace('_', ' ')}</h3>
            <div class="mt-2 space-x-2">
                <a href="/ui/test_assessment/{category}" 
                   class="inline-block px-3 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600">
                   Test Form
                </a>
                <a href="/ui/test_report/{category}" 
                   class="inline-block px-3 py-1 bg-green-500 text-white rounded text-sm hover:bg-green-600">
                   Test Report
                </a>
            </div>
        </div>
        '''
    
    html += '''
        </div>
    </div>
    '''
    
    return HTMLResponse(html)