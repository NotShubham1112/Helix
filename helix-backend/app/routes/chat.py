from fastapi import APIRouter, HTTPException
from app.models.schemas import ChatRequest, ChatResponse
from app.services.orchestrator import route_request
from app.utils.helpers import get_timestamp

router = APIRouter()

@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process chat message and return AI response.
    """
    try:
        # Route the request based on intent
        result = route_request(
            input_data={"message": request.message},
            user_input=request.message
        )
        
        if result.get("status") != "success":
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        # Extract reply from analysis
        analysis = result.get("data", {})
        reply = analysis.get("summary", "Unable to process your request")
        
        return ChatResponse(
            reply=reply,
            intent=result.get("intent", "general_chat"),
            confidence=analysis.get("confidence", 0.5)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """
    Stream chat response (for real-time UI updates).
    """
    try:
        result = route_request(
            input_data={"message": request.message},
            user_input=request.message
        )
        
        if result.get("status") != "success":
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        analysis = result.get("data", {})
        
        return {
            "reply": analysis.get("summary", "Unable to process"),
            "intent": result.get("intent"),
            "confidence": analysis.get("confidence", 0.5),
            "timestamp": get_timestamp()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-symptoms")
async def analyze_symptoms(request: ChatRequest):
    """
    Analyze patient symptoms with medical reasoning.
    """
    try:
        # Route as symptom query
        result = route_request(
            input_data={"symptoms": request.message},
            user_input=request.message
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
