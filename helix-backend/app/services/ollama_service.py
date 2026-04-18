"""
Ollama Local Model Service

Handles all interactions with local Ollama models.
Supports both streaming and non-streaming responses.
"""

import requests
import json
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_API_GENERATE = f"{OLLAMA_BASE_URL}/api/generate"
OLLAMA_API_PULL = f"{OLLAMA_BASE_URL}/api/pull"
OLLAMA_API_TAGS = f"{OLLAMA_BASE_URL}/api/tags"

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
    def get_available_models() -> list:
        """Get list of available models."""
        try:
            response = requests.get(OLLAMA_API_TAGS, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
            return []
        except Exception as e:
            logger.error(f"Error fetching models: {e}")
            return []
    
    @staticmethod
    def call_model(
        model: str,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.3,
        context: Optional[str] = None,
        timeout: int = 60
    ) -> str:
        """
        Call a local Ollama model.
        
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
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "temperature": temperature,
            }
            
            if system:
                payload["system"] = system
            
            if context:
                payload["context"] = context
            
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
                return f"Error: {response.status_code}"
                
        except requests.exceptions.Timeout:
            logger.error(f"Ollama timeout for model {model}")
            return "Error: Request timeout"
        except Exception as e:
            logger.error(f"Ollama call error: {e}")
            return f"Error: {str(e)}"
    
    @staticmethod
    def call_model_streaming(
        model: str,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.3,
    ):
        """
        Stream response from Ollama model.
        Yields chunks of response as they arrive.
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
            logger.error(f"Ollama streaming error: {e}")
            yield f"Error: {str(e)}"
    
    @staticmethod
    def parse_json_response(response: str) -> Dict[str, Any]:
        """
        Extract and parse JSON from model response.
        """
        try:
            # Try direct JSON parsing
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from text
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
    def warmup_model(model: str) -> bool:
        """
        Warmup a model by running a simple inference.
        Loads model into VRAM for faster subsequent calls.
        
        Args:
            model: Model name
        
        Returns:
            True if warmup successful
        """
        try:
            logger.info(f"Warming up model: {model}")
            response = OllamaService.call_model(
                model,
                "Confirm you are ready.",
                timeout=120
            )
            success = bool(response) and "error" not in response.lower()
            if success:
                logger.info(f"✓ Model {model} warmed up")
            else:
                logger.warning(f"✗ Model {model} warmup may have failed")
            return success
        except Exception as e:
            logger.error(f"Model warmup error: {e}")
            return False
    
    @staticmethod
    def pull_model(model: str) -> bool:
        """
        Pull (download) a model from Ollama registry.
        
        Args:
            model: Model name
        
        Returns:
            True if successful
        """
        try:
            logger.info(f"Pulling model: {model}")
            response = requests.post(
                OLLAMA_API_PULL,
                json={"name": model},
                timeout=3600  # Long timeout for download
            )
            success = response.status_code == 200
            if success:
                logger.info(f"✓ Model {model} pulled successfully")
            else:
                logger.error(f"Pull failed: {response.status_code}")
            return success
        except Exception as e:
            logger.error(f"Model pull error: {e}")
            return False
