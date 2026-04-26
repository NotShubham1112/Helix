from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import logging
from datetime import datetime
from app.models.schemas import ChatRequest, ChatResponse
from app.services.rag_service import RAGService
from app.services.llm_service import call_llm
from app.db.supabase_client import get_supabase
from app.dependencies.auth import get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter()

CHAT_SYSTEM_PROMPT = """
You are HELIX, a healthcare AI assistant. Your role is to answer questions about medical reports.

IMPORTANT RULES:
1. NEVER provide medical advice or diagnoses
2. ALWAYS encourage consulting with healthcare providers
3. Use the provided report context to answer questions
4. Be clear about what you do NOT know
5. Maintain patient safety and privacy

When answering:
- Reference the report data provided
- Explain what values mean in simple terms
- Suggest discussing with doctors for next steps
- Do NOT guess or speculate
"""


@router.post("/", response_model=ChatResponse)
async def chat_with_report(
    request: ChatRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    Chat about a specific report with RAG context retrieval.
    
    Process:
    1. Get report data
    2. Retrieve user's past context (RAG)
    3. Combine: report + rag + question
    4. Call LLM for answer
    5. Store conversation
    
    Args:
        request: ChatRequest with message and report_id
        user_id: Authenticated user ID
    
    Returns:
        ChatResponse with answer
    """
    try:
        report_id = request.report_id
        message = request.message

        logger.info(f"Chat request from user {user_id} on report {report_id}")

        # Step 1: Get report
        supabase = get_supabase()
        report = supabase.get_report(report_id, user_id)

        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        # Step 2: Retrieve RAG context
        rag_context = RAGService.retrieve_for_chat(user_id, message, k=5)

        # Step 3: Build prompt
        report_summary = f"""
REPORT DATA:
- Summary: {report.get('parsed_data', {}).get('summary', 'N/A')}
- Lab Values: {report.get('parsed_data', {}).get('values', {})}
- Abnormalities: {report.get('analysis_result', {}).get('abnormalities', [])}

USER QUESTION: {message}

{f'RELEVANT PAST CONTEXT:{rag_context}' if rag_context else ''}
"""

        prompt = f"""{CHAT_SYSTEM_PROMPT}

{report_summary}

Please answer the user's question about their report. Remember to:
1. Use the data from the report
2. Reference past context if relevant
3. Do NOT diagnose
4. Encourage consulting healthcare providers
"""

        # Step 4: Call LLM
        logger.info("Calling LLM for response")
        response_text = call_llm(
            prompt=prompt,
            model="auto",
            use_ollama=True
        )

        # Step 5: Store conversation
        message_id = supabase.create_chat_message(
            report_id=report_id,
            user_id=user_id,
            message=message,
            response=response_text,
            metadata={
                "model": "gemma:4b",
                "context_items": len(rag_context.split("\n")) if rag_context else 0
            }
        )

        logger.info(f"Chat response generated: {message_id}")

        return ChatResponse(
            message_id=message_id or f"msg_{datetime.utcnow().timestamp()}",
            reply=response_text,
            confidence=0.85,
            context_used=len(rag_context.split("\n")) if rag_context else 0
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat request failed: {e}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@router.get("/{report_id}/history")
async def get_chat_history(
    report_id: str,
    user_id: str = Depends(get_current_user_id),
    limit: int = 50
):
    """
    Get chat history for a report.
    
    Args:
        report_id: Report identifier
        user_id: Authenticated user ID
        limit: Maximum messages
    
    Returns:
        List of chat messages
    """
    try:
        supabase = get_supabase()

        # Verify user has access to report
        report = supabase.get_report(report_id, user_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        # Get chat history
        messages = supabase.get_chat_history(report_id, user_id, limit)

        return {
            "status": "success",
            "count": len(messages),
            "messages": messages
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{report_id}/history")
async def clear_chat_history(
    report_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Clear chat history for a report.
    
    Args:
        report_id: Report identifier
        user_id: Authenticated user ID
    
    Returns:
        Deletion status
    """
    try:
        supabase = get_supabase()

        # Verify user has access to report
        report = supabase.get_report(report_id, user_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        # Delete chat messages
        if supabase.is_available():
            supabase.client.table("chat_messages").delete().eq(
                "report_id", report_id
            ).eq("user_id", user_id).execute()

        logger.info(f"Cleared chat history for report {report_id}")

        return {
            "status": "success",
            "message": "Chat history cleared"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to clear chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        
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
