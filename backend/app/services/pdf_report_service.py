# app/services/pdf_report_service.py
from fpdf import FPDF
from datetime import datetime
from app.services.schemas import SessionData, FinalReport # Import your Pydantic models

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Miraat - Confidential Wellness Summary', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_pdf_from_report(session_data: SessionData, final_report: FinalReport) -> bytes:
    """
    Takes the final SessionData and the structured FinalReport object and renders them into a PDF.
    
    Returns:
        The PDF content as bytes.
    """
    pdf = PDF()
    pdf.add_page()
    pdf.set_font('Arial', '', 12)

    # --- Report Metadata ---
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Session Details', 0, 1)
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 8, f"Session ID: {session_data.session_id}", 0, 1)
    pdf.cell(0, 8, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 0, 1)
    pdf.ln(8)

    # --- Section 1: Opening Summary ---
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'An Empathetic Summary', 0, 1)
    pdf.set_font('Arial', '', 11)
    pdf.multi_cell(0, 6, final_report.opening_summary)
    pdf.ln(8)
    
    # --- Section 2: Assessment Findings ---
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Assessment Findings', 0, 1)
    pdf.set_font('Arial', '', 11)
    pdf.multi_cell(0, 6, final_report.assessment_findings)
    pdf.ln(8)

    # --- Section 3: Recommended Steps ---
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Recommended Next Steps', 0, 1)
    pdf.set_font('Arial', '', 11)
    pdf.multi_cell(0, 6, final_report.recommended_steps)
    pdf.ln(8)

    # --- Section 4: Disclaimer ---
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Important Disclaimer', 0, 1)
    pdf.set_font('Arial', 'I', 9)
    pdf.multi_cell(0, 5, final_report.disclaimer)
    
    # Return the PDF content as bytes
    return pdf.output(dest='S').encode('latin-1')