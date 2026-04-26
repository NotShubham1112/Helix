from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging
import re
import base64
from app.services.mvp_hba1c import run_pipeline, MvpHba1cResponse
from app.services.ocr_engine import ocr_engine
from app.services.llm_service import call_llm
from app.services.ollama_service import OllamaService

logger = logging.getLogger(__name__)
router = APIRouter()

class AnalyzeRequest(BaseModel):
    ocr_text: str

class GenerateReportRequest(BaseModel):
    text: str

class GenerateReportResponse(BaseModel):
    summary_report: str
    full_report: str

class ChatRequest(BaseModel):
    question: str
    report: str

class ChatResponse(BaseModel):
    answer: str

# ─── Prompts ────────────────────────────────────────────────────────────────

REPORT_PROMPT = """You are a clinical report generator.

Generate TWO outputs for the medical data provided below:

1. FULL_REPORT (1000–1500 words):
- Highly detailed, deep clinical analysis.
- Include all relevant interpretations, pathophysiology context, and detailed clinical rationale.
- Use structured sections: Title, Patient Summary, Key Findings, Interpretation, Recommendations.
- Provide evidence-backed professional tone.

2. SUMMARY_REPORT (400–600 words):
- Clean, readable, and concise.
- Suitable for high-level UI display.
- Use structured sections: Title, Patient Summary, Key Findings, Interpretation, Recommendations.

Rules:
- Do NOT hallucinate values. Mention missing data clearly if necessary.
- NO asterisks (*), NO markdown bolding, NO hashes (#), NO preamble.
- Format EXACTLY as a JSON object with keys "full_report" and "summary_report".

Input:
{text}

Return JSON:
{{
  "full_report": "...",
  "summary_report": "..."
}}"""

CHAT_PROMPT = """You are Helix, a medical assistant. Answer using ONLY this report:
{report}

Rules:
- Use rich Markdown formatting (e.g., bullet points, bold text).
- Be concise. If not in report, say so.
- No medical advice/diagnoses.

Question: {question}
Answer:"""

# ─── Endpoints ─────────────────────────────────────────────────────────────

@router.post("/analyze-report", response_model=MvpHba1cResponse)
async def analyze_report(request: AnalyzeRequest):
    try:
        return run_pipeline(request.ocr_text)
    except Exception as e:
        logger.error(f"Error in analyze_report: {e}")
        return MvpHba1cResponse(status="failed", error=str(e))

@router.post("/analyze-image", response_model=MvpHba1cResponse)
async def analyze_image(file: UploadFile = File(...)):
    """Extract clinical text from image via Vision LLM."""
    try:
        content = await file.read()
        b64_image = base64.b64encode(content).decode("utf-8")
        
        logger.info("Using Vision LLM (Qwen-VL) to analyze medical image...")
        
        from app.services.model_router import ModelRouter, TaskType
        prompt = "Extract all clinical text from this medical report exactly as written. Return ONLY the text."
        
        # Use Qwen-VL via the router
        ocr_text = OllamaService.call_ollama(
            model=ModelRouter.get_model_for_task(TaskType.VISION_ANALYSIS),
            prompt=prompt,
            images=[b64_image],
            temperature=0.0,
            timeout=180
        )
        
        if not ocr_text or ocr_text.startswith("Error:"):
            logger.warning("Vision LLM failed, using mock OCR.")
            ocr_text = ocr_engine.perform_ocr(content)

        return run_pipeline(ocr_text)
    except Exception as e:
        logger.error(f"Error in analyze_image: {e}")
        return MvpHba1cResponse(status="failed", error=str(e))

@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "Helix Local MVP v1"}

@router.post("/generate-report")
async def generate_report(request: GenerateReportRequest):
    """Generates dual detailed report outputs in JSON format (~2000 words total)."""
    try:
        from app.services.model_router import ModelRouter, TaskType
        model = ModelRouter.get_model_for_task(TaskType.DEEP_REASONING)
        prompt = REPORT_PROMPT.format(text=request.text.strip())
        raw_json = OllamaService.call_ollama(model=model, prompt=prompt, temperature=0.3, timeout=300)
        parsed = OllamaService.parse_json_response(raw_json)
        return GenerateReportResponse(
            full_report=parsed.get("full_report", raw_json),
            summary_report=parsed.get("summary_report", raw_json)
        )
    except Exception as e:
        logger.error(f"Error: {e}"); raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-report-stream")
async def generate_report_stream(request: GenerateReportRequest):
    """Streams the FULL report first (~1500 words), then '---SUM---', then the SUMMARY (~500 words)."""
    from fastapi.responses import StreamingResponse
    from app.services.model_router import ModelRouter, TaskType
    async def stream_generator():
        try:
            model = ModelRouter.get_model_for_task(TaskType.DEEP_REASONING)
            stream_prompt = (
                "You are a clinical report generator. "
                "Generate a detailed ~1500 word clinical report based on the data below. "
                "Then output exactly '---SUM---'. "
                "Then generate a ~500 word summary version.\n\n"
                "RULES FOR BOTH REPORTS:\n"
                "- NO preamble. Output exactly as requested.\n"
                "- You MUST use EXACTLY these exact section headers, each on their own line:\n"
                "Title\nPatient Summary\nKey Findings\nInterpretation\nRecommendations\n\n"
                f"Data: {request.text.strip()}"
            )
            for chunk in OllamaService.call_model_streaming(model=model, prompt=stream_prompt, temperature=0.3):
                if chunk: yield chunk
        except Exception as e:
            logger.error(f"Stream error: {e}"); yield f"Error: {str(e)}"
    return StreamingResponse(stream_generator(), media_type="text/plain")

@router.post("/chat", response_model=ChatResponse)
async def report_chat(request: ChatRequest):
    try:
        prompt = CHAT_PROMPT.format(report=request.report.strip(), question=request.question.strip())
        answer = call_llm(prompt=prompt, model="auto", use_ollama=True)
        return ChatResponse(answer=answer.strip())
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat-stream")
async def report_chat_stream(request: ChatRequest):
    from fastapi.responses import StreamingResponse
    from app.services.model_router import ModelRouter, TaskType

    async def stream_generator():
        try:
            model = ModelRouter.get_model_for_task(TaskType.FAST_RESPONSE)
            prompt = CHAT_PROMPT.format(report=request.report.strip(), question=request.question.strip())
            for chunk in OllamaService.call_model_streaming(model=model, prompt=prompt, temperature=0.1):
                if chunk: yield chunk
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"Error: {str(e)}"

    return StreamingResponse(stream_generator(), media_type="text/plain")
