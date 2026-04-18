"""
Backend Startup & Initialization

Handles:
- Ollama auto-start
- Model warmup
- System initialization
- Health checks
"""

import subprocess
import time
import sys
import logging
import platform
from typing import List
from app.services.ollama_service import OllamaService

logger = logging.getLogger(__name__)

# Model configuration
MODELS_TO_LOAD = [
    "nemotron:4b",      # Router model
    "gemma:4b",         # Reasoning model
]

# Expected availability
OLLAMA_STARTUP_TIME = 3  # seconds
MODEL_WARMUP_TIMEOUT = 120  # seconds per model


class SystemInitializer:
    """Handles system initialization and health checks."""
    
    @staticmethod
    def start_ollama() -> bool:
        """
        Start Ollama service.
        
        Returns:
            True if Ollama started or was already running
        """
        logger.info("🚀 Starting Ollama service...")
        
        # Check if already running
        if OllamaService.is_available():
            logger.info("✓ Ollama is already running")
            return True
        
        try:
            # Start Ollama based on OS
            system = platform.system()
            
            if system == "Darwin":  # macOS
                subprocess.Popen([
                    "/Applications/Ollama.app/Contents/MacOS/ollama",
                    "serve"
                ])
            elif system == "Windows":
                # On Windows, Ollama runs as a service
                # Try to ensure it's running
                subprocess.Popen(["ollama", "serve"])
            else:  # Linux
                subprocess.Popen(["ollama", "serve"])
            
            # Wait for Ollama to be ready
            logger.info(f"⏳ Waiting for Ollama to start ({OLLAMA_STARTUP_TIME}s)...")
            time.sleep(OLLAMA_STARTUP_TIME)
            
            # Verify it's running
            if OllamaService.is_available():
                logger.info("✓ Ollama started successfully")
                return True
            else:
                logger.warning("⚠ Ollama may not be ready yet")
                return False
                
        except FileNotFoundError:
            logger.error("✗ Ollama not found. Please install Ollama from https://ollama.ai")
            return False
        except Exception as e:
            logger.error(f"✗ Error starting Ollama: {e}")
            return False
    
    @staticmethod
    def check_models() -> List[str]:
        """
        Check which required models are available.
        
        Returns:
            List of available models
        """
        logger.info("🔍 Checking available models...")
        available = OllamaService.get_available_models()
        
        if not available:
            logger.warning("⚠ No models found locally")
            return []
        
        logger.info(f"Found models: {available}")
        return available
    
    @staticmethod
    def ensure_models_available() -> bool:
        """
        Ensure all required models are available.
        Pull models if missing.
        
        Returns:
            True if all models are available or successfully pulled
        """
        logger.info("📦 Ensuring models are available...")
        
        available = OllamaService.get_available_models()
        success = True
        
        for model in MODELS_TO_LOAD:
            if not any(model in available_model for available_model in available):
                logger.warning(f"Model {model} not found, attempting to pull...")
                if not OllamaService.pull_model(model):
                    logger.error(f"Failed to pull model {model}")
                    success = False
            else:
                logger.info(f"✓ Model {model} available")
        
        return success
    
    @staticmethod
    def warmup_models() -> bool:
        """
        Warmup all models by running inference.
        Loads models into VRAM for low-latency access.
        
        Returns:
            True if all models warmed up successfully
        """
        logger.info("🔥 Warming up models...")
        
        all_success = True
        for model in MODELS_TO_LOAD:
            logger.info(f"Warming up {model}...")
            
            if not OllamaService.warmup_model(model):
                logger.warning(f"⚠ Failed to warmup {model}")
                all_success = False
            else:
                logger.info(f"✓ {model} ready")
        
        return all_success
    
    @staticmethod
    def health_check() -> dict:
        """
        Perform comprehensive health check.
        
        Returns:
            Health check results
        """
        logger.info("🏥 Running health checks...")
        
        health = {
            "ollama": OllamaService.is_available(),
            "models": {},
            "status": "healthy"
        }
        
        # Check each model
        for model in MODELS_TO_LOAD:
            try:
                response = OllamaService.call_model(
                    model,
                    "ping",
                    timeout=10
                )
                health["models"][model] = bool(response) and "error" not in response.lower()
            except Exception as e:
                health["models"][model] = False
                logger.error(f"Health check failed for {model}: {e}")
        
        # Overall status
        if not health["ollama"] or not all(health["models"].values()):
            health["status"] = "degraded"
        
        return health
    
    @staticmethod
    def initialize() -> bool:
        """
        Complete system initialization.
        
        Returns:
            True if initialization successful
        """
        logger.info("\n" + "="*60)
        logger.info("HELIX Backend Initialization")
        logger.info("="*60 + "\n")
        
        try:
            # Step 1: Start Ollama
            if not SystemInitializer.start_ollama():
                logger.error("Failed to start Ollama")
                return False
            
            # Step 2: Check models
            SystemInitializer.check_models()
            
            # Step 3: Ensure models available
            if not SystemInitializer.ensure_models_available():
                logger.warning("⚠ Some models may not be available")
            
            # Step 4: Warmup models
            if not SystemInitializer.warmup_models():
                logger.warning("⚠ Some models may not be warmed up")
            
            # Step 5: Health check
            health = SystemInitializer.health_check()
            logger.info(f"Health Status: {health['status']}")
            
            logger.info("\n" + "="*60)
            logger.info("✓ HELIX Backend Ready!")
            logger.info("="*60 + "\n")
            
            return health["status"] == "healthy"
            
        except Exception as e:
            logger.error(f"✗ Initialization failed: {e}")
            return False


async def async_initialize():
    """Async wrapper for initialization (for FastAPI startup event)."""
    logger.info("Starting async initialization...")
    return SystemInitializer.initialize()
