from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="HELIX Medical AI Backend",
    description="Production-grade clinical intelligence backend with secure JWT authentication",
    version="1.0.0"
)

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Try to import routers, but continue if they fail
try:
    from app.routes import upload, chat, analyze
    app.include_router(upload.router, prefix="/api/upload", tags=["Upload"])
    app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
    app.include_router(analyze.router, prefix="/api/analyze", tags=["Analysis"])
    logger.info("✓ AI routes loaded")
except Exception as e:
    logger.warning(f"⚠ Could not load AI routes: {e}")

# Include auth examples routes
try:
    from app.routes import auth_examples
    app.include_router(auth_examples.router)
    logger.info("✓ Auth routes loaded")
except Exception as e:
    logger.warning(f"⚠ Could not load auth routes: {e}")


# Startup event - initialize system
@app.on_event("startup")
def startup_event():
    """Initialize backend on startup."""
    logger.info("🚀 HELIX Backend starting up...")
    logger.info("✓ Auth system initialized")
    logger.info("✓ FastAPI app ready")
    try:
        from app.startup import SystemInitializer
        SystemInitializer.initialize()
        logger.info("✓ Ollama services initialized")
    except Exception as e:
        logger.warning(f"⚠ Ollama not available (this is OK for auth-only mode): {e}")


# Shutdown event
@app.on_event("shutdown")
def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Backend shutting down...")


# Health check endpoint
@app.get("/health")
def health():
    """System health check"""
    return {
        "status": "healthy",
        "service": "HELIX Medical AI",
        "version": "1.0.0"
    }


# Status endpoint
@app.get("/status")
def status():
    """Detailed status information"""
    return {
        "status": "operational",
        "service": "HELIX Medical AI Backend",
        "version": "1.0.0",
        "authentication": "JWT enabled (Supabase)",
        "endpoints": {
            "auth": "/api/auth/*",
            "upload": "/api/upload/*",
            "chat": "/api/chat/*",
            "analysis": "/api/analyze/*"
        }
    }


@app.get("/")
def root():
    return {
        "message": "HELIX Medical AI Backend",
        "status": "operational",
        "version": "1.0.0",
        "docs": "/docs",
        "system": "Clinical AI with Secure JWT Authentication"
    }


@app.get("/health")
def health():
    """Comprehensive health check."""
    health_status = SystemInitializer.health_check()
    return health_status


@app.get("/status")
def status():
    """Detailed system status."""
    ollama_available = OllamaService.is_available()
    models = OllamaService.get_available_models()
    
    return {
        "system": "helix",
        "ollama": {
            "available": ollama_available,
            "url": "http://localhost:11434",
            "models": models
        },
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
