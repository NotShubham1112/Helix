from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.ocr_service import extract_text, validate_lab_values
from app.models.schemas import UploadResponse
from app.utils.helpers import get_timestamp

router = APIRouter()

@router.post("/", response_model=UploadResponse)
async def upload_report(file: UploadFile = File(...)):
    """
    Upload and process a medical report (PDF, Image, etc.)
    """
    try:
        # Read file content
        content = await file.read()
        
        # Extract text using OCR
        extracted = extract_text(content)
        
        # Validate extracted lab values
        if extracted.get("status") == "error":
            raise HTTPException(status_code=400, detail=extracted.get("error"))
        
        validation = validate_lab_values(extracted)
        
        return UploadResponse(
            status="processed",
            data=validation,
            message=f"Successfully processed {file.filename}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze")
async def analyze_upload(file: UploadFile = File(...)):
    """
    Upload and immediately analyze a medical report
    """
    try:
        content = await file.read()
        extracted = extract_text(content)
        
        if extracted.get("status") == "error":
            raise HTTPException(status_code=400, detail=extracted.get("error"))
        
        # Analyze the extracted data
        from app.services.reasoning_service import analyze_health
        analysis = analyze_health(extracted)
        
        return {
            "filename": file.filename,
            "analysis": analysis,
            "timestamp": get_timestamp()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
