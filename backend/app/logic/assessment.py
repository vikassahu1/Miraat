from fastapi import APIRouter, Depends, HTTPException
from app.services.schemas import SessionData, AssessmentRequest, AssessmentSubmitRequest,TestData
from app.services.assessment_service import AssessmentService


def start_assessment(
    request: AssessmentRequest,
    assessment_service: AssessmentService
)->TestData:
    """
    Given a final category from the conversation, this endpoint returns the
    full test (questions and options) to be rendered by the UI.
    """
    test_data = assessment_service.get_assessment_for_category(request.final_category)
    if not test_data or not test_data.test_data:
        raise HTTPException(status_code=404, detail=f"No test found for category: {request.final_category}")
    
    return test_data


def submit_assessment(
    request: AssessmentSubmitRequest,
    assessment_service: AssessmentService
) -> SessionData:
    """
    Receives the full set of answers, scores them, and returns the
    final, completed SessionData object containing the full report.
    """
    session_data = request.session_data
    answers = request.answers
    
    if session_data.status != "assessing":
        raise HTTPException(status_code=400, detail="Session is not in the assessing state.")

    # This single function call does all the work..append ans in summary of AssementReport schema 
    completed_session_data = assessment_service.score_and_conclude_assessment(
        session_data, answers
    )
    
    return completed_session_data