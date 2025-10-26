import json
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import List
from core_logic.Accessories.logger import logging
# Import your services, DB session, and models
from app.services.security_service import EncryptionService
from app.services.pdf_report_service import generate_pdf_from_report
from app.services.report_service import FinalReportService
from core_logic.Data.database import TestHistory
from main import get_db # Your function to get a DB session
from app.services.schemas import SessionData # Your Pydantic model

router = APIRouter()

# --- Dependency Injection (will be wired in main.py) ---
def get_encryption_service() -> EncryptionService:
    raise NotImplementedError

def get_report_service() -> FinalReportService: 
    raise NotImplementedError("Service dependency not properly injected")

# --- API Endpoints ---

@router.get("/user-history", summary="Fetch all test history for a user")
def get_user_history(
    username: str = Query(..., alias="user_name"), 
    db: Session = Depends(get_db)
):
    """
    Fetches a list of all test sessions for a given username.
    Returns only non-sensitive data (ID and date).
    """
    history_records = db.query(TestHistory.test_id, TestHistory.date).filter(TestHistory.user_name == username).order_by(TestHistory.date.desc()).all()
    
    if not history_records:
        return []
        
    return [{"test_id": record.test_id, "date": record.date.isoformat()} for record in history_records]


@router.get("/{test_id}/report", summary="Generate and download a decrypted PDF report")
def download_decrypted_report(
    test_id: int,
    username: str = Query(..., alias="user_name"),
    db: Session = Depends(get_db),
    encryption_service: EncryptionService = Depends(get_encryption_service),
    report_service: FinalReportService = Depends(get_report_service) # Inject the report generator
):
    """
    Fetches a specific test record, decrypts its data, regenerates the structured report,
    creates a PDF, and returns it for download.
    """
    record = db.query(TestHistory).filter(TestHistory.test_id == test_id, TestHistory.user_name == username).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="Test history not found.")

    # 1. Decrypt the full session data
    try:
        logging.info(f"Retrieved encrypted_session_data type: {type(record.encrypted_session_data)}")
        logging.info(f"Retrieved encrypted_session_data length: {len(record.encrypted_session_data) if hasattr(record.encrypted_session_data, '__len__') else 'unknown'}")
        logging.info(f"First 50 chars: {str(record.encrypted_session_data)[:50]}")
        
        # Decrypt the entire session data JSON
        decrypted_session_json = encryption_service.decrypt_data(record.encrypted_session_data)
        session_data_dict = json.loads(decrypted_session_json)
        
        # 2. Decrypt the nested encrypted fields BEFORE creating the Pydantic object
        
        # a) Decrypt conversation history
        if "conversation_history" in session_data_dict:
            decrypted_history = []
            for turn in session_data_dict["conversation_history"]:
                decrypted_content = encryption_service.decrypt_data(turn["content"])
                decrypted_history.append({"role": turn["role"], "content": decrypted_content})
            session_data_dict["conversation_history"] = decrypted_history
        
        # b) Decrypt the narrative report
        if (session_data_dict.get("assessment_data") and 
            session_data_dict["assessment_data"].get("narrative_report") and
            isinstance(session_data_dict["assessment_data"]["narrative_report"], str)):
            
            encrypted_report = session_data_dict["assessment_data"]["narrative_report"]
            decrypted_report_json = encryption_service.decrypt_data(encrypted_report)
            session_data_dict["assessment_data"]["narrative_report"] = json.loads(decrypted_report_json)
        
        # 3. Now create the Pydantic object with fully decrypted data
        session_data = SessionData(**session_data_dict)
        
    except Exception as e:
        logging.error(f"Decryption failed for test_id {test_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to decrypt session data.")

    # 2. Regenerate the structured FinalReport object using your existing service
    # This ensures the report is always up-to-date with your latest prompts/logic
    # In history.py, after line 99:

    try:
        structured_report = report_service.generate_final_report(session_data)
        logging.info("Report generated successfully, proceeding to PDF generation...")
    except Exception as e:
        logging.error(f"Report generation failed for test_id {test_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate structured report.")

    # 3. Generate the PDF using the new PDF service
    try:
        logging.info("Starting PDF generation...")
        pdf_bytes = generate_pdf_from_report(session_data, structured_report)
        logging.info(f"PDF generated successfully. Size: {len(pdf_bytes)} bytes")
    except Exception as e:
        logging.error(f"PDF generation failed for test_id {test_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate PDF.")

    # 4. Return the PDF as a downloadable file
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=miraat_summary_{test_id}.pdf"}
    )



@router.delete("/{test_id}", summary="Delete a test history record")
def delete_test_history(
    test_id: int,
    username: str = Query(..., alias="user_name"),
    db: Session = Depends(get_db)
):
    """Deletes a specific test record owned by the user."""
    record = db.query(TestHistory).filter(TestHistory.test_id == test_id, TestHistory.user_name == username).first()

    if not record:
        raise HTTPException(status_code=404, detail="Test history not found or you do not have permission to delete it.")

    db.delete(record)
    db.commit()
    return {"status": "success", "message": f"Test ID {test_id} deleted successfully."}