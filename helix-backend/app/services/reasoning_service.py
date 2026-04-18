from app.services.llm_service import call_llm, structured_llm_call
from app.prompts.clinical_prompt import CLINICAL_PROMPT
from app.utils.helpers import format_medical_data, check_hallucination, get_timestamp
from typing import Dict, Any

def analyze_health(data: Dict[str, Any], context: str = "") -> Dict[str, Any]:
    """
    Analyze patient health data using clinical reasoning.
    
    Args:
        data: Patient medical data (lab values, vitals, etc.)
        context: Additional clinical context or retrieved documents
    
    Returns:
        Structured analysis with risks and recommendations
    """
    
    # Format data for LLM
    formatted_data = format_medical_data(data)
    
    # Build prompt
    prompt = CLINICAL_PROMPT.format(
        data=formatted_data,
        context=context if context else "No additional context available"
    )
    
    # Get LLM response
    response = call_llm(prompt)
    
    # Check for hallucinations
    if check_hallucination(response):
        return {
            "error": "Safety check failed - potential hallucination detected",
            "summary": "Unable to provide analysis due to safety concerns",
            "abnormalities": [],
            "risks": [],
            "recommendations": [
                {
                    "action": "Please consult a healthcare provider",
                    "urgency": "High"
                }
            ],
            "confidence": 0.0,
            "timestamp": get_timestamp()
        }
    
    # Parse response into structured format
    analysis = parse_clinical_response(response)
    
    return analysis

def parse_clinical_response(response: str) -> Dict[str, Any]:
    """
    Parse LLM response into structured format.
    """
    try:
        # Simple parsing - in production use more robust method
        lines = response.split("\n")
        
        result = {
            "summary": extract_section(lines, "Summary"),
            "abnormalities": extract_list_section(lines, "Abnormalities"),
            "risks": extract_risks_section(lines, "Risks"),
            "recommendations": extract_recommendations_section(lines, "Recommendations"),
            "confidence": extract_confidence(lines),
            "timestamp": get_timestamp()
        }
        
        return result
        
    except Exception as e:
        return {
            "error": f"Failed to parse response: {str(e)}",
            "raw_response": response,
            "timestamp": get_timestamp()
        }

def extract_section(lines: list, section_name: str) -> str:
    """Extract a text section from response."""
    for i, line in enumerate(lines):
        if section_name.lower() in line.lower():
            return lines[i].split(":", 1)[-1].strip() if ":" in line else ""
    return ""

def extract_list_section(lines: list, section_name: str) -> list:
    """Extract a list section from response."""
    items = []
    in_section = False
    
    for line in lines:
        if section_name.lower() in line.lower():
            in_section = True
            continue
        
        if in_section and line.strip().startswith("-"):
            items.append(line.strip()[1:].strip())
        elif in_section and line.strip() == "":
            continue
        elif in_section and not line.strip().startswith("-"):
            break
    
    return items

def extract_risks_section(lines: list, section_name: str) -> list:
    """Extract risks in structured format."""
    risks = []
    for abnormality in extract_list_section(lines, section_name):
        parts = abnormality.split("-")
        risk = {
            "condition": parts[0].strip() if len(parts) > 0 else "",
            "probability": parts[1].strip() if len(parts) > 1 else "Unknown",
            "reason": parts[2].strip() if len(parts) > 2 else ""
        }
        risks.append(risk)
    
    return risks

def extract_recommendations_section(lines: list, section_name: str) -> list:
    """Extract recommendations in structured format."""
    recommendations = []
    
    for rec in extract_list_section(lines, section_name):
        recommendation = {
            "action": rec,
            "urgency": "Medium"  # Default urgency
        }
        
        # Check for urgency keywords
        rec_lower = rec.lower()
        if "urgent" in rec_lower or "immediately" in rec_lower or "emergency" in rec_lower:
            recommendation["urgency"] = "High"
        elif "soon" in rec_lower or "within" in rec_lower:
            recommendation["urgency"] = "Medium"
        else:
            recommendation["urgency"] = "Low"
        
        recommendations.append(recommendation)
    
    return recommendations

def extract_confidence(lines: list) -> float:
    """Extract confidence score from response."""
    for line in lines:
        if "confidence" in line.lower():
            try:
                # Try to extract number
                parts = line.split(":")
                if len(parts) > 1:
                    value = float(parts[1].strip())
                    return min(max(value, 0.0), 1.0)  # Clamp to 0-1
            except:
                pass
    
    return 0.5  # Default confidence
