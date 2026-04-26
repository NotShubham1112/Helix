from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

# ============== Upload Endpoints ==============

class UploadResponse(BaseModel):
    """Response for file upload."""
    status: str
    report_id: str
    message: str
    file_name: str
    processed_at: str


# ============== Chat Endpoints ==============

class ChatRequest(BaseModel):
    """Chat message request."""
    message: str
    report_id: str


class ChatResponse(BaseModel):
    """Chat response."""
    message_id: str
    reply: str
    confidence: float
    context_used: int


# ============== Report Endpoints ==============

class LabValue(BaseModel):
    """Single lab value."""
    value: float
    unit: str
    status: str  # normal, high, low
    normal_range: str


class Abnormality(BaseModel):
    """Abnormal finding."""
    test: str
    value: float
    unit: str
    status: str
    range: str


class RiskIndicator(BaseModel):
    """Risk indicator."""
    type: str
    indicator: str
    severity: str  # low, moderate, high


class HelixReport(BaseModel):
    """HELIX report structure."""
    summary: str
    abnormalities: List[str]
    risk_assessment: List[str]
    recommendations: List[str]
    confidence: float


class ReportResponse(BaseModel):
    """Complete report response."""
    id: str
    user_id: str
    created_at: str
    file_name: str
    summary: str
    abnormalities: List[str]
    risk_assessment: List[str]
    recommendations: List[str]
    confidence: float
    total_values: int
    abnormal_values: int


class ReportHistoryResponse(BaseModel):
    """Report in history list."""
    id: str
    created_at: str
    file_name: str
    status: str
    abnormal_count: int


# ============== Error Responses ==============

class ErrorResponse(BaseModel):
    """Standard error response."""
    status: str
    error: str
    detail: Optional[str] = None


# ============== Legacy Compatibility ==============

class ChatRequest_Legacy(BaseModel):
    message: str
    context: Optional[str] = None


class Risk(BaseModel):
    condition: str
    probability: str
    reason: str


class Recommendation(BaseModel):
    action: str
    urgency: str


class AnalyzeRequest(BaseModel):
    data: dict
    patient_id: Optional[str] = None


class AnalyzeResponse(BaseModel):
    analysis: HelixReport
    timestamp: str


class HelixResponse(BaseModel):
    """Generic HELIX response wrapper used across services."""
    status: str
    report: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: Optional[str] = None
