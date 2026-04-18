from fastapi import APIRouter, HTTPException
from app.models.schemas import AnalyzeRequest, AnalyzeResponse
from app.services.reasoning_service import analyze_health
from app.services.rag_service import analyze_with_rag
from app.utils.helpers import get_timestamp
from typing import Optional

router = APIRouter()

@router.post("/", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    """
    Analyze medical data and return clinical insights.
    """
    try:
        # Perform analysis with RAG context
        analysis = analyze_with_rag(request.data)
        
        if "error" in analysis:
            raise HTTPException(status_code=400, detail=analysis.get("error"))
        
        return AnalyzeResponse(
            analysis=analysis,
            timestamp=get_timestamp()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/labs")
async def analyze_labs(request: AnalyzeRequest):
    """
    Analyze laboratory test results.
    """
    try:
        # Validate lab values
        from app.services.ocr_service import validate_lab_values
        validation = validate_lab_values(request.data)
        
        # Analyze abnormalities
        analysis = analyze_health(validation.get("data", request.data))
        
        return {
            "validation": validation,
            "analysis": analysis,
            "timestamp": get_timestamp()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/drugs")
async def analyze_drugs(request: AnalyzeRequest):
    """
    Analyze drug information and interactions.
    """
    try:
        from app.services.drug_service import (
            get_drug_info,
            check_drug_interactions,
            get_drug_contraindications
        )
        
        drugs = request.data.get("drugs", [])
        conditions = request.data.get("conditions", [])
        
        results = {
            "drugs": [],
            "interactions": [],
            "contraindications": [],
            "timestamp": get_timestamp()
        }
        
        # Analyze each drug
        for drug in drugs:
            info = get_drug_info(drug)
            results["drugs"].append(info)
            
            if conditions:
                contra = get_drug_contraindications(drug, conditions)
                results["contraindications"].extend(contra.get("contraindications", []))
        
        # Check interactions
        if len(drugs) > 1:
            interactions = check_drug_interactions(drugs)
            results["interactions"] = interactions.get("interactions", [])
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/full-assessment")
async def full_assessment(request: AnalyzeRequest):
    """
    Perform comprehensive health assessment.
    """
    try:
        # Multi-faceted analysis
        lab_analysis = None
        drug_analysis = None
        
        if "labs" in request.data:
            from app.services.ocr_service import validate_lab_values
            validation = validate_lab_values(request.data["labs"])
            lab_analysis = analyze_health(validation.get("data", {}))
        
        if "drugs" in request.data:
            from app.services.drug_service import check_drug_interactions
            drug_analysis = check_drug_interactions(request.data["drugs"])
        
        general_analysis = analyze_with_rag(request.data)
        
        return {
            "labs": lab_analysis,
            "drugs": drug_analysis,
            "general": general_analysis,
            "patient_id": request.patient_id,
            "timestamp": get_timestamp()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
