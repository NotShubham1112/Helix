"""
Ollama Service - Production Grade

Handles all Ollama interactions with:
- Robust error handling
- Timeout management
- Safe warmup with memory awareness
- Health checking
- Model verification
"""

import requests
import json
import logging
import time
from typing import Optional, Dict, Any, Generator
from app.config.models import (
    OLLAMA_BASE_URL,
    OLLAMA_MAX_RETRIES,
    OLLAMA_RETRY_DELAY,
    WARMUP_TIMEOUT,
    WARMUP_PROMPT,
    WARMUP_DELAY,
)

logger = logging.getLogger(__name__)

OLLAMA_API_TAGS = f"{OLLAMA_BASE_URL}/api/tags"
OLLAMA_API_GENERATE = f"{OLLAMA_BASE_URL}/api/generate"
OLLAMA_API_PULL = f"{OLLAMA_BASE_URL}/api/pull"


class OllamaService:
    """Service for calling local Ollama models."""

    @staticmethod
    def is_available() -> bool:
        """Check if Ollama is running."""
        try:
            response = requests.get(
                f"{OLLAMA_BASE_URL}/api/tags",
                timeout=2
            )
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    @staticmethod
    def wait_for_ollama(max_retries: int = None, retry_delay: int = None) -> bool:
        """
        Poll for Ollama availability.

        Args:
            max_retries: Max retry attempts (default from config)
            retry_delay: Delay between retries in seconds (default from config)

        Returns:
            True if Ollama becomes available
        """
        if max_retries is None:
            max_retries = OLLAMA_MAX_RETRIES
        if retry_delay is None:
            retry_delay = OLLAMA_RETRY_DELAY

        logger.info(f"⏳ Waiting for Ollama API (up to {max_retries * retry_delay}s)...")

        for attempt in range(max_retries):
            try:
                response = requests.get(
                    OLLAMA_API_TAGS,
                    timeout=2
                )
                if response.status_code == 200:
                    logger.info(f"✓ Ollama ready (attempt {attempt + 1})")
                    return True
            except requests.exceptions.RequestException:
                pass

            if attempt < max_retries - 1:
                time.sleep(retry_delay)

        logger.error("✗ Ollama API did not become available")
        return False

    @staticmethod
    def get_available_models() -> list:
        """
        Get list of available models from Ollama.

        Returns:
            List of model names
        """
        try:
            response = requests.get(OLLAMA_API_TAGS, timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = [model["name"] for model in data.get("models", [])]
                logger.info(f"📦 Found models: {models}")
                return models
            return []
        except Exception as e:
            logger.error(f"Error fetching models: {e}")
            return []

    @staticmethod
    def verify_models_exist(required_models: list) -> bool:
        """
        Verify that required models exist in Ollama.

        Args:
            required_models: List of model names to check

        Returns:
            True if all models exist
        """
        available = OllamaService.get_available_models()

        all_exist = True
        for model in required_models:
            if model in available:
                logger.info(f"✓ Model found: {model}")
            else:
                logger.error(f"✗ Model NOT found: {model}")
                logger.error(f"  Available models: {available}")
                all_exist = False

        return all_exist

    @staticmethod
    def warmup_model(model: str) -> bool:
        """
        Warmup a model by running a simple inference.

        Args:
            model: Model name (MUST match ollama list exactly)

        Returns:
            True if warmup successful
        """
        try:
            logger.info(f"Warming up {model}...")

            payload = {
                "model": model,
                "prompt": WARMUP_PROMPT,
                "stream": False,
                "temperature": 0.1,
            }

            response = requests.post(
                OLLAMA_API_GENERATE,
                json=payload,
                timeout=WARMUP_TIMEOUT
            )

            if response.status_code == 200:
                data = response.json()
                if "response" in data:
                    logger.info(f"✓ Warmed model: {model}")
                    return True

            logger.error(f"Ollama warmup error: {response.status_code}")
            return False

        except requests.exceptions.Timeout:
            logger.error(f"✗ Warmup timeout for {model} ({WARMUP_TIMEOUT}s)")
            return False
        except Exception as e:
            logger.error(f"✗ Warmup error for {model}: {e}")
            return False

    @staticmethod
    def call_ollama(
        model: str,
        prompt: str,
        system: Optional[str] = None,
        images: Optional[list[str]] = None,
        temperature: float = 0.3,
        timeout: int = 60,
    ) -> str:
        """
        Call Ollama with error handling.

        Args:
            model: Model name
            prompt: Input prompt
            system: Optional system prompt
            temperature: Model temperature
            timeout: Request timeout in seconds

        Returns:
            Model response or error message
        """
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "temperature": temperature,
            }

            if system:
                payload["system"] = system
            
            if images:
                payload["images"] = images

            response = requests.post(
                OLLAMA_API_GENERATE,
                json=payload,
                timeout=timeout
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("response", "")
            else:
                logger.error(f"Ollama error: {response.status_code}")
                return f"Error: HTTP {response.status_code}"

        except requests.exceptions.Timeout:
            logger.error(f"Timeout calling {model} ({timeout}s)")
            return "Error: Request timeout"
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error to Ollama")
            return "Error: Connection failed"
        except Exception as e:
            logger.error(f"Call error: {e}")
            return f"Error: {str(e)}"

    @staticmethod
    def call_model(
        model: str,
        prompt: str,
        system: Optional[str] = None,
        images: Optional[list[str]] = None,
        temperature: float = 0.3,
        context: Optional[str] = None,
        timeout: int = 60
    ) -> str:
        """
        Call a local Ollama model (legacy method, use call_ollama).
        
        Args:
            model: Model name (e.g., "gemma:4b")
            prompt: The prompt to send
            system: System prompt for context
            temperature: Model temperature (0-1)
            context: Optional context window
            timeout: Request timeout in seconds
        
        Returns:
            Model response text
        """
        return OllamaService.call_ollama(model, prompt, system, images, temperature, timeout)
    
    @staticmethod
    def call_model_streaming(
        model: str,
        prompt: str,
        system: Optional[str] = None,
        images: Optional[list[str]] = None,
        temperature: float = 0.3,
    ) -> Generator[str, None, None]:
        """
        Stream response from Ollama model.

        Args:
            model: Model name
            prompt: Input prompt
            system: Optional system prompt
            temperature: Model temperature

        Yields:
            Response chunks
        """
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": True,
                "temperature": temperature,
            }

            if system:
                payload["system"] = system
            
            if images:
                payload["images"] = images

            response = requests.post(
                OLLAMA_API_GENERATE,
                json=payload,
                stream=True,
                timeout=300
            )

            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if "response" in data:
                                yield data["response"]
                        except json.JSONDecodeError:
                            continue
            else:
                yield f"Error: {response.status_code}"

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"Error: {str(e)}"
    
    @staticmethod
    def parse_json_response(response: str) -> Dict[str, Any]:
        """
        Extract and parse JSON from model response.

        Args:
            response: Raw response from model

        Returns:
            Parsed JSON or error dict
        """
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass

            return {
                "error": "Failed to parse response as JSON",
                "raw_response": response
            }
    
    @staticmethod
    def pull_model(model: str) -> bool:
        """
        Pull a model from Ollama registry.

        Args:
            model: Model name to pull

        Returns:
            True if pull successful
        """
        try:
            logger.info(f"Pulling model: {model}")
            response = requests.post(
                OLLAMA_API_PULL,
                json={"name": model},
                timeout=600
            )

            if response.status_code == 200:
                logger.info(f"✓ Model {model} pulled successfully")
                return True
            else:
                logger.error(f"Failed to pull {model}: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Pull error: {e}")
            return False

