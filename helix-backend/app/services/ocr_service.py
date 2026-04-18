from typing import Dict, Any
import base64

def extract_text(file_bytes: bytes) -> Dict[str, Any]:
    """
    Extract text from medical reports using GLM-OCR.
    
    Args:
        file_bytes: The binary content of the uploaded file
    
    Returns:
        Dictionary with extracted medical data
    """
    try:
        # Placeholder for actual GLM-OCR implementation
        # In production, integrate with actual OCR API
        
        # For now, return mock lab values
        extracted_data = {
            "hemoglobin": "10 g/dL",
            "hematocrit": "30%",
            "glucose": "140 mg/dL",
            "creatinine": "1.2 mg/dL",
            "blood_pressure": "140/90 mmHg",
            "heart_rate": "78 bpm",
            "status": "extracted"
        }
        
        return extracted_data
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

def validate_lab_values(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate extracted lab values against normal ranges.
    """
    normal_ranges = {
        "hemoglobin": {"min": 12.0, "max": 17.5, "unit": "g/dL"},
        "glucose": {"min": 70, "max": 100, "unit": "mg/dL"},
        "creatinine": {"min": 0.6, "max": 1.2, "unit": "mg/dL"},
        "hematocrit": {"min": 36, "max": 46, "unit": "%"}
    }
    
    abnormalities = []
    
    for key, value in data.items():
        if key in normal_ranges:
            try:
                # Simple numeric extraction
                numeric_value = float(value.split()[0])
                normal = normal_ranges[key]
                
                if numeric_value < normal["min"] or numeric_value > normal["max"]:
                    abnormalities.append({
                        "test": key,
                        "value": value,
                        "status": "abnormal"
                    })
            except:
                pass
    
    return {
        "data": data,
        "abnormalities": abnormalities,
        "is_normal": len(abnormalities) == 0
    }
