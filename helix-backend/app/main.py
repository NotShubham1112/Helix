from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="HELIX Medical AI Backend",
    description="Healthcare data analysis backend with OpenRouter LLM",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3002",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


try:
    from app.routes import upload, chat, report, analyze
    app.include_router(upload.router, prefix="/api/upload", tags=["Upload"])
    app.include_router(report.router, prefix="/api/report", tags=["Report"])
    app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
    app.include_router(analyze.router, prefix="/api/analyze", tags=["Analysis"])
    logger.info("AI routes loaded")
except Exception as e:
    logger.warning(f"Could not load AI routes: {e}")

try:
    from app.routes import auth_examples
    app.include_router(auth_examples.router)
    logger.info("Auth routes loaded")
except Exception as e:
    logger.warning(f"Could not load auth routes: {e}")

try:
    from app.routes import mvp
    app.include_router(mvp.router, prefix="/api/mvp", tags=["MVP"])
    logger.info("MVP routes loaded")
except Exception as e:
    logger.warning(f"Could not load MVP routes: {e}")


@app.on_event("startup")
def startup_event():
    logger.info("HELIX Backend starting up...")
    demo = os.getenv("DEMO_MODE", "true").lower() == "true"
    if demo:
        logger.info("Running in DEMO MODE (no JWT auth required)")

    try:
        from app.services.ollama_init import OllamaInitializer
        OllamaInitializer.initialize()
        logger.info("Ollama services initialized")
    except Exception as e:
        logger.warning(f"Ollama not available, will use OpenRouter fallback: {e}")


@app.on_event("shutdown")
def shutdown_event():
    logger.info("Backend shutting down...")


@app.get("/")
def root():
    return {
        "message": "HELIX Medical AI Backend",
        "status": "operational",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "HELIX Medical AI",
        "version": "1.0.0"
    }


@app.get("/status")
def status():
    ollama_available = False
    models = []
    try:
        from app.services.ollama_service import OllamaService
        ollama_available = OllamaService.is_available()
        models = OllamaService.get_available_models()
    except Exception:
        pass

    return {
        "status": "operational",
        "service": "HELIX Medical AI Backend",
        "version": "1.0.0",
        "ollama": {
            "available": ollama_available,
            "models": models
        },
        "openrouter": {
            "configured": bool(os.getenv("OPENROUTER_API_KEY"))
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
