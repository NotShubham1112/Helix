import re
import math
from typing import Literal, Optional
from pydantic import BaseModel, Field

# Ensure we have access to ollama. Use fallback try/except in case not installed
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

# ==============================================================================
# SCHEMA
# ==============================================================================

class Parameter(BaseModel):
    name: Literal["HbA1c", "Glucose"]
    value: float
    unit: str
    confidence: float = Field(ge=0.0, le=1.0)
    source_text: str

class Interpretation(BaseModel):
    category: Literal["Normal", "Prediabetes", "Diabetes", "Unknown"]
    message: str
    requires_medical_attention: bool

class MvpHba1cResponse(BaseModel):
    status: Literal["success", "partial_success", "failed"]
    parameter: Optional[Parameter] = None
    interpretation: Optional[Interpretation] = None
    warning: Optional[str] = None
    error: Optional[str] = None
    ocr_text: Optional[str] = None


# ==============================================================================
# EXTRACTION LOGIC
# ==============================================================================

def extract_regex(text: str) -> dict | None:
    """
    Deterministically extract HbA1c values using RegEx.
    """
    pattern = r"(?i)(?:hba1c|a1c|glycosylated\s+hemoglobin)[\s\:\-\=]*(\d{1,2}\.\d{1,2})[\s]*(\%)"
    match = re.search(pattern, text)
    if match:
        val, unit = match.groups()
        start = max(0, match.start() - 20)
        end = min(len(text), match.end() + 20)
        source_text = text[start:end].replace('\n', ' ').strip()
        return {
            "name": "HbA1c",
            "value": float(val),
            "unit": "%",
            "confidence": 0.95, 
            "source_text": source_text
        }
    return None

def extract_llm_fallback(text: str) -> dict | None:
    """
    Fallback extraction using a local quantized LLM for zero-hallucination extraction.
    """
    if not OLLAMA_AVAILABLE:
        return None
        
    prompt = f"""
    Extract ONLY the HbA1c value and its unit from the text below. 
    Strict rules:
    1. If HbA1c is not found, reply exactly with "NULL".
    2. Do NOT invent missing values.
    3. Format output as: VALUE|UNIT|EXACT_SOURCE_QUOTE

    Text:
    "{text}"
    """
    try:
        from app.services.model_router import ModelRouter, TaskType
        model_name = ModelRouter.get_model_for_task(TaskType.FAST_RESPONSE)
        response = ollama.chat(model=model_name, messages=[{'role': 'user', 'content': prompt}])
        content = response['message']['content'].strip()
        if "NULL" in content.upper() or "|" not in content:
            return None
        
        parts = content.split('|')
        if len(parts) >= 3:
            return {
                "name": "HbA1c",
                "value": float(parts[0]),
                "unit": parts[1].strip(),
                "confidence": 0.60,
                "source_text": parts[2].strip()
            }
    except Exception as e:
        print(f"LLM fallback failed: {e}")
        pass
    
    return None

def extract_hba1c(text: str) -> dict | None:
    """
    Hybrid extraction pipeline.
    """
    res = extract_regex(text)
    if res:
         return res
    return extract_llm_fallback(text)


# ==============================================================================
# VALIDATION LAYER
# ==============================================================================

def validate_extraction(raw_data: dict, ocr_full_text: str) -> Parameter | None:
    """
    Enforces valid parsed schemas and performs anti-hallucination checks against the source text.
    """
    if not raw_data:
        return None
        
    try:
        param = Parameter(**raw_data)
        
        # Anti-Hallucination check: ensure source_text exists in original OCR text
        clean_source = "".join(filter(str.isalnum, param.source_text.lower()))
        clean_ocr = "".join(filter(str.isalnum, ocr_full_text.lower()))
        
        if clean_source not in clean_ocr:
            raise ValueError("Hallucination detected: Source text not found in original document.")
            
        return param
    except Exception as e:
        print(f"Validation error: {e}")
        return None

# ==============================================================================
# PIPELINE RUNNER
# ==============================================================================

def run_pipeline(ocr_text: str) -> MvpHba1cResponse:
    """
    Unified entry point for text and image-based analysis.
    """
    if not ocr_text or not ocr_text.strip():
        return MvpHba1cResponse(status="failed", error="OCR text is empty or failed", ocr_text=ocr_text)
        
    extracted_data = extract_hba1c(ocr_text)
    parameter = validate_extraction(extracted_data, ocr_text)
    
    if not parameter:
        return MvpHba1cResponse(status="failed", error="Could not extract valid HbA1c parameter.", ocr_text=ocr_text)
        
    interpretation = interpret_hba1c(parameter.value)
    
    # Failure Handling: Low confidence warning
    warning = None
    if parameter.confidence < 0.8:
        warning = "Low confidence extraction. Please verify results against original report."
        
    return MvpHba1cResponse(
        status="success",
        parameter=parameter,
        interpretation=interpretation,
        warning=warning,
        ocr_text=ocr_text
    )
def interpret_hba1c(value: float) -> Interpretation:
    """
    Deterministic interpretation without LLM context.
    """
    if math.isnan(value) or value < 4.0 or value > 20.0:
        return Interpretation(
            category="Unknown",
            message="Value is outside physiologically expected ranges. Please review the report manually.",
            requires_medical_attention=True
        )
        
    if value < 5.7:
        return Interpretation(
            category="Normal",
            message="HbA1c is within the normal range.",
            requires_medical_attention=False
        )
    elif 5.7 <= value <= 6.4:
        return Interpretation(
            category="Prediabetes",
            message="HbA1c indicates prediabetes. Lifestyle modifications may be recommended.",
            requires_medical_attention=True
        )
    else:
        return Interpretation(
            category="Diabetes",
            message="HbA1c is in the diabetic range. Please consult a healthcare provider.",
            requires_medical_attention=True
        )
