"""
Ollama Initialization - Production Grade

Handles:
- Ollama startup
- Health checks with retries
- Model verification
- Sequential model warmup (memory-safe)
- Complete initialization pipeline
"""

import subprocess
import time
import platform
import logging
from typing import List
from app.services.ollama_service import OllamaService
from app.config.models import (
    WARMUP_MODELS,
    WARMUP_DELAY,
)

logger = logging.getLogger(__name__)

OLLAMA_STARTUP_WAIT = 3  # seconds to wait after starting


class OllamaInitializer:
    """Handles Ollama initialization and startup."""

    @staticmethod
    def start_ollama() -> bool:
        """
        Start Ollama service.

        Returns:
            True if Ollama started or was already running
        """
        logger.info("Starting Ollama...")

        # Check if already running
        if OllamaService.is_available():
            logger.info("✓ Ollama is already running")
            return True

        try:
            system = platform.system()

            if system == "Darwin":  # macOS
                subprocess.Popen(
                    ["/Applications/Ollama.app/Contents/MacOS/ollama", "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            elif system == "Windows":
                # Windows: Ollama typically runs as a service
                try:
                    subprocess.Popen(
                        ["ollama", "serve"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                except FileNotFoundError:
                    logger.error(
                        "✗ Ollama not found. Please install from https://ollama.ai"
                    )
                    return False
            else:  # Linux
                subprocess.Popen(
                    ["ollama", "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

            logger.info(f"⏳ Waiting {OLLAMA_STARTUP_WAIT}s for Ollama to start...")
            time.sleep(OLLAMA_STARTUP_WAIT)

            if OllamaService.is_available():
                logger.info("✓ Ollama started successfully")
                return True
            else:
                logger.warning("⚠ Ollama may not be fully ready yet")
                return False

        except Exception as e:
            logger.error(f"✗ Error starting Ollama: {e}")
            return False

    @staticmethod
    def verify_models(models: List[str]) -> bool:
        """
        Verify that required models exist.

        Args:
            models: List of model names to verify

        Returns:
            True if all models exist
        """
        logger.info("Verifying models...")

        return OllamaService.verify_models_exist(models)

    @staticmethod
    def warmup_models(models: List[str]) -> bool:
        """
        Warmup models sequentially with delays for memory safety.

        Args:
            models: List of model names to warmup

        Returns:
            True if all models warmed successfully
        """
        logger.info("🔥 Warming up models sequentially...")

        all_success = True
        for i, model in enumerate(models):
            if OllamaService.warmup_model(model):
                logger.info(f"✓ Warmed {model} ({i + 1}/{len(models)})")
            else:
                logger.warning(f"⚠ Warmup failed for {model}")
                all_success = False

            # Add delay between warmups for memory safety
            if i < len(models) - 1:
                logger.info(f"⏳ Waiting {WARMUP_DELAY}s before next warmup...")
                time.sleep(WARMUP_DELAY)

        return all_success

    @staticmethod
    def health_check() -> dict:
        """
        Perform comprehensive health check.

        Returns:
            Health status dict
        """
        logger.info("Running health checks...")

        health = {
            "ollama": OllamaService.is_available(),
            "models": {},
            "status": "healthy",
        }

        for model in WARMUP_MODELS:
            try:
                response = OllamaService.call_ollama(
                    model, "OK", timeout=60
                )
                health["models"][model] = "error" not in response.lower()
            except Exception:
                health["models"][model] = False

        if not health["ollama"] or not all(health["models"].values()):
            health["status"] = "degraded"

        logger.info(f"Health Status: {health['status']}")
        return health

    @staticmethod
    def initialize() -> bool:
        """
        Complete Ollama initialization pipeline.

        Flow:
        1. Start Ollama
        2. Wait for API readiness
        3. Verify models exist
        4. Warmup models sequentially
        5. Health check

        Returns:
            True if initialization successful
        """
        logger.info("\n" + "=" * 60)
        logger.info("OLLAMA INITIALIZATION")
        logger.info("=" * 60 + "\n")

        try:
            # Step 1: Start Ollama
            if not OllamaInitializer.start_ollama():
                logger.error("✗ Failed to start Ollama")
                return False

            # Step 2: Wait for API readiness
            if not OllamaService.wait_for_ollama():
                logger.error("✗ Ollama API did not become ready")
                return False

            # Step 3: Verify models exist
            if not OllamaInitializer.verify_models(WARMUP_MODELS):
                logger.error("✗ Required models not found")
                return False

            # Step 4: Warmup models
            if not OllamaInitializer.warmup_models(WARMUP_MODELS):
                logger.warning("⚠ Some models failed to warmup")

            # Step 5: Health check
            health = OllamaInitializer.health_check()

            logger.info("\n" + "=" * 60)
            logger.info("✓ OLLAMA READY")
            logger.info("=" * 60 + "\n")

            return health["status"] == "healthy"

        except Exception as e:
            logger.error(f"✗ Initialization failed: {e}")
            return False
