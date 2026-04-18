from typing import Dict, Any
from app.services.router_service import classify_intent
from app.services.reasoning_service import analyze_health
from app.services.rag_service import analyze_with_rag
from app.services.drug_service import get_drug_info, check_drug_interactions
from app.services.ocr_service import validate_lab_values
from app.utils.helpers import get_timestamp

def route_request(input_data: Dict[str, Any], user_input: str = None) -> Dict[str, Any]:
    """
    Route request to appropriate service based on intent.
    
    Args:
        input_data: Patient/query data
        user_input: User's text input (for intent classification)
    
    Returns:
        Processed response from appropriate service
    """
    
    # Classify intent
    intent = classify_intent(user_input or str(input_data))
    
    result = {
        "intent": intent,
        "timestamp": get_timestamp()
    }
    
    try:
        if intent == "lab_report":
            # Validate lab values and analyze
            validation = validate_lab_values(input_data)
            analysis = analyze_health(validation["data"])
            result["data"] = analysis
            result["validation"] = validation
            
        elif intent == "prescription":
            # Check drug interactions and contraindications
            if "drugs" in input_data:
                interactions = check_drug_interactions(input_data["drugs"])
                result["interactions"] = interactions
            
            if "drug_info" in input_data:
                drug_info = get_drug_info(input_data["drug_info"])
                result["drug_data"] = drug_info
        
        elif intent == "imaging":
            # Future: X-ray/imaging analysis
            result["data"] = analyze_health(input_data)
            
        elif intent == "symptom_query":
            # Symptom analysis with RAG
            result["data"] = analyze_with_rag(input_data)
            
        else:
            # General chat
            result["data"] = analyze_health(input_data)
        
        result["status"] = "success"
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
    
    return result

def process_batch(requests: list) -> list:
    """
    Process multiple requests in batch.
    
    Args:
        requests: List of request data
    
    Returns:
        List of processed results
    """
    results = []
    for req in requests:
        result = route_request(req.get("data"), req.get("input"))
        results.append(result)
    
    return results
