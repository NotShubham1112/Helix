from pydantic import BaseModel
from typing import List, Optional

# Request Models
class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = None

class UploadRequest(BaseModel):
    filename: str
    content: str

class AnalyzeRequest(BaseModel):
    data: dict
    patient_id: Optional[str] = None

# Response Models
class Risk(BaseModel):
    condition: str
    probability: str
    reason: str

class Recommendation(BaseModel):
    action: str
    urgency: str

class HelixResponse(BaseModel):
    summary: str
    abnormalities: List[str]
    risks: List[Risk]
    recommendations: List[Recommendation]
    confidence: float

class ChatResponse(BaseModel):
    reply: str
    intent: str
    confidence: float

class UploadResponse(BaseModel):
    status: str
    data: dict
    message: str

class AnalyzeResponse(BaseModel):
    analysis: HelixResponse
    timestamp: str
