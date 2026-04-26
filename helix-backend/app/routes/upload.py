from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import Optional
import logging
from datetime import datetime
from app.models.schemas import UploadResponse
from app.services.ocr_service import extract_text
from app.services.parser_service import ParserService
from app.services.report_service import ReportService
from app.services.rag_service import RAGService
from app.db.supabase_client import get_supabase
from app.dependencies.auth import get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=UploadResponse)
async def upload_and_process(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id)
):
    """
    Upload medical document and process through complete pipeline:
    1. Save to Supabase Storage
    2. Extract text via OCR
    3. Parse and normalize values
    4. Generate report via LLM
    5. Store in vector memory
    6. Return report_id
    
    Args:
        file: Medical document (PDF, image)
        user_id: Authenticated user ID
    
    Returns:
        UploadResponse with report_id
    """
    try:
        # Step 1: Read file
        file_content = await file.read()
        if not file_content:
            raise HTTPException(status_code=400, detail="Empty file")

        logger.info(f"Processing upload for user {user_id}: {file.filename}")

        # Step 2: Upload to Supabase Storage
        supabase = get_supabase()
        file_url = supabase.upload_file(user_id, file_content, file.filename)
        logger.info(f"File uploaded to storage: {file_url}")

        # Step 3: Extract text via OCR
        extracted_data = extract_text(file_content)
        if extracted_data.get("status") == "error":
            raise HTTPException(status_code=400, detail=f"OCR failed: {extracted_data.get('error')}")

        extracted_data["extracted_at"] = datetime.utcnow().isoformat()
        logger.info(f"Extracted data: {len(extracted_data)} fields")

        # Step 4: Parse and normalize values
        parsed_data = ParserService.normalize_extracted_data(extracted_data)
        logger.info(f"Parsed {parsed_data['summary']['total_tests']} lab values")

        # Step 5: Create report in Supabase
        report_id = supabase.create_report(
            user_id=user_id,
            file_name=file.filename,
            file_url=file_url or "",
            parsed_data=parsed_data
        )

        if not report_id:
            report_id = f"report_{datetime.utcnow().timestamp()}"

        logger.info(f"Created report record: {report_id}")

        # Step 6: Generate report via LLM
        report_result = ReportService.generate_report(
            user_id=user_id,
            parsed_data=parsed_data,
            report_id=report_id,
            file_metadata={"filename": file.filename, "size": len(file_content)}
        )

        if report_result["status"] != "success":
            raise HTTPException(status_code=500, detail="Report generation failed")

        report_data = report_result["report"]

        # Step 7: Update report status
        supabase.update_report_status(
            report_id=report_id,
            status="completed",
            analysis_result=report_data.get("report")
        )

        # Step 8: Store in vector memory for future chat
        import json
        report_text = f"""
Report: {report_data['report'].get('summary', '')}
Abnormalities: {json.dumps(report_data['report'].get('abnormalities', []))}
Recommendations: {json.dumps(report_data['report'].get('recommendations', []))}
"""
        RAGService.add_report_to_memory(user_id, report_id, report_text)
        logger.info(f"Added report to vector memory for user {user_id}")

        # Step 9: Return response
        return UploadResponse(
            status="success",
            report_id=report_id,
            message=f"Report generated successfully",
            file_name=file.filename,
            processed_at=datetime.utcnow().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.get("/{report_id}")
async def get_report(
    report_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Get a previously generated report.
    
    Args:
        report_id: Report identifier
        user_id: Authenticated user ID
    
    Returns:
        Report data
    """
    try:
        supabase = get_supabase()
        report = supabase.get_report(report_id, user_id)

        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        return {
            "status": "success",
            "report": report
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_reports(
    user_id: str = Depends(get_current_user_id),
    limit: int = 50
):
    """
    List all reports for authenticated user.
    
    Args:
        user_id: Authenticated user ID
        limit: Maximum reports to return
    
    Returns:
        List of reports
    """
    try:
        supabase = get_supabase()
        reports = supabase.get_user_reports(user_id, limit)

        return {
            "status": "success",
            "count": len(reports),
            "reports": reports
        }

    except Exception as e:
        logger.error(f"Failed to list reports: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        
        return {
            "filename": file.filename,
            "analysis": analysis,
            "timestamp": get_timestamp()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
