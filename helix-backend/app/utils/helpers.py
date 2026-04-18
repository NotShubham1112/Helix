import json
from typing import Any, Dict
from datetime import datetime

def validate_json_output(response: str) -> Dict[str, Any]:
    """
    Validate and parse JSON output from LLM.
    Returns parsed JSON or error dict if invalid.
    """
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        return {"error": "Invalid JSON output from model"}

def check_hallucination(text: str) -> bool:
    """
    Check for common hallucination patterns in clinical output.
    Returns True if text contains hallucination patterns.
    """
    forbidden_patterns = [
        "you have diagnosed",
        "confirmed disease",
        "you definitely have",
        "100% certain",
        "guaranteed",
        "will definitely",
        "cure"
    ]
    
    text_lower = text.lower()
    for pattern in forbidden_patterns:
        if pattern in text_lower:
            return True
    
    return False

def sanitize_medical_output(text: str) -> str:
    """
    Remove potentially harmful language from medical output.
    """
    replacements = {
        "diagnosis": "clinical finding",
        "diagnosed": "indicated",
        "disease confirmed": "clinical indication",
    }
    
    for key, value in replacements.items():
        text = text.replace(key, value)
    
    return text

def get_timestamp() -> str:
    """Get current ISO timestamp."""
    return datetime.utcnow().isoformat()

def format_medical_data(data: Dict) -> str:
    """Format medical data for LLM consumption."""
    formatted = []
    for key, value in data.items():
        formatted.append(f"{key}: {value}")
    return "\n".join(formatted)
