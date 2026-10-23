"""
CryptoScope Reports API Router
Endpoint:
- POST /api/reports/{id}?format=pdf|json|html
- GET /api/reports/{id}?format=pdf|json|html
"""

import json
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.models import AnalysisModel
from backend.app.reports.generator import generate_html_report, generate_pdf_report
from backend.app.api.analysis_router import ANALYSIS_CACHE

router = APIRouter(prefix="/reports", tags=["Reports"])

REPORTS_DIR = settings.BASE_DIR / "backend" / "data" / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

def _get_analysis_data(analysis_id: str, db: Session):
    # Check in-memory cache first
    if analysis_id in ANALYSIS_CACHE:
        return ANALYSIS_CACHE[analysis_id]["full_data"]
    
    # Query database
    row = db.query(AnalysisModel).filter(AnalysisModel.id == analysis_id).first()
    if not row:
        raise HTTPException(status_code=404, detail=f"Analysis '{analysis_id}' not found.")
    
    try:
        data = json.loads(row.full_data_json)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse analysis data: {str(e)}")

@router.post("/{id}")
@router.get("/{id}")
def export_report(
    id: str,
    format: str = Query("json", pattern="^(pdf|json|html)$"),
    db: Session = Depends(get_db)
):
    """
    Exports a firmware security audit report in PDF, HTML, or JSON format.
    Contains architecture profile, recovered primitives, protocol graphs,
    defensive vulnerability advisories, and paper caveats.
    """
    analysis_data = _get_analysis_data(id, db)

    if format == "json":
        return JSONResponse(content=analysis_data)
    
    elif format == "html":
        html_content = generate_html_report(analysis_data)
        return HTMLResponse(content=html_content, media_type="text/html")
    
    elif format == "pdf":
        pdf_file = REPORTS_DIR / f"cryptoscope_report_{id}.pdf"
        try:
            generate_pdf_report(analysis_data, pdf_file)
            return FileResponse(
                path=str(pdf_file),
                media_type="application/pdf",
                filename=f"cryptoscope_report_{id}.pdf"
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

    raise HTTPException(status_code=400, detail="Unsupported format. Choose 'pdf', 'html', or 'json'.")
