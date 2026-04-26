"""
Smart Model Routing

Intelligently routes tasks to appropriate models based on:
- Task complexity
- Response time requirements
- Model availability
- Performance characteristics
"""

import logging
from enum import Enum
from typing import Literal
from app.services.ollama_service import OllamaService

logger = logging.getLogger(__name__)


class TaskType(str, Enum):
    """Task classification for routing."""
    ROUTING = "routing"                    # Intent classification
    FAST_RESPONSE = "fast_response"        # Quick responses
    DEEP_REASONING = "deep_reasoning"      # Complex analysis
    LAB_ANALYSIS = "lab_analysis"
    DRUG_ANALYSIS = "drug_analysis"
    SYMPTOM_ANALYSIS = "symptom_analysis"
    EMERGENCY_DETECTION = "emergency"
    VISION_ANALYSIS = "vision_analysis"  # Multimodal extraction


class ModelRouter:
    """Routes tasks to optimal models."""
    
    # Model assignments by task type
    ROUTING_MAP = {
        TaskType.ROUTING: "nemotron-3-nano:4b",           # Fast classification
        TaskType.FAST_RESPONSE: "nemotron-3-nano:4b",     # Quick turnaround
        TaskType.DEEP_REASONING: "gemma4:e2b",       # Deep analysis
        TaskType.LAB_ANALYSIS: "gemma4:e2b",         # Medical knowledge
        TaskType.DRUG_ANALYSIS: "gemma4:e2b",        # Pharmacology
        TaskType.SYMPTOM_ANALYSIS: "gemma4:e2b",     # Clinical reasoning
        TaskType.EMERGENCY_DETECTION: "nemotron-3-nano:4b",  # Fast flag
        TaskType.VISION_ANALYSIS: "qwen3-vl:8b"     # Multimodal/OCR
    }
    
    # Model configuration
    MODEL_CONFIG = {
        "nemotron-3-nano:4b": {
            "latency": "low",
            "accuracy": "medium",
            "use_cases": ["routing", "classification", "fast response"],
            "temperature": 0.3,
            "max_tokens": 512
        },
        "gemma4:e2b": {
            "latency": "medium",
            "accuracy": "high",
            "use_cases": ["reasoning", "analysis", "context"],
            "temperature": 0.2,
            "max_tokens": 2048
        }
    }
    
    @staticmethod
    def get_model_for_task(task_type: TaskType) -> str:
        """
        Get optimal model for task.
        
        Args:
            task_type: Type of task
        
        Returns:
            Model name
        """
        return ModelRouter.ROUTING_MAP.get(task_type, "gemma4:e2b")
    
    @staticmethod
    def get_config_for_model(model: str) -> dict:
        """Get configuration for model."""
        return ModelRouter.MODEL_CONFIG.get(
            model,
            {
                "latency": "unknown",
                "accuracy": "unknown",
                "temperature": 0.3,
                "max_tokens": 1024
            }
        )
    
    @staticmethod
    def call_task(
        task_type: TaskType,
        prompt: str,
        system_prompt: str = None,
        fallback_to_openrouter: bool = True
    ) -> str:
        """
        Execute task with optimal model.
        
        Args:
            task_type: Type of task
            prompt: The prompt
            system_prompt: System context
            fallback_to_openrouter: Fall back to OpenRouter if Ollama unavailable
        
        Returns:
            Model response
        """
        logger.info(f"Routing task: {task_type}")
        
        # Check if Ollama available
        if not OllamaService.is_available():
            logger.warning("Ollama not available, falling back to OpenRouter")
            if fallback_to_openrouter:
                return ModelRouter._call_openrouter(prompt, system_prompt)
            else:
                return '{"error": "Model service unavailable"}'
        
        # Get appropriate model
        model = ModelRouter.get_model_for_task(task_type)
        config = ModelRouter.get_config_for_model(model)
        
        logger.info(f"Using model: {model} (latency: {config['latency']})")
        
        # Call model
        try:
            response = OllamaService.call_model(
                model=model,
                prompt=prompt,
                system=system_prompt,
                temperature=config.get("temperature", 0.3),
                timeout=60
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Model call failed: {e}")
            
            # Try fallback
            if fallback_to_openrouter:
                logger.info("Falling back to OpenRouter")
                return ModelRouter._call_openrouter(prompt, system_prompt)
            else:
                return f'{{"error": "Model error: {str(e)}"}}'
    
    @staticmethod
    def _call_openrouter(prompt: str, system_prompt: str = None) -> str:
        """
        Fallback to OpenRouter API.
        """
        import requests
        import os
        
        try:
            api_key = os.getenv("OPENROUTER_API_KEY")
            if not api_key:
                return '{"error": "OpenRouter API key not configured"}'
            
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "qwen/qwen3-32b",
                    "messages": [
                        {"role": "system", "content": system_prompt or "You are a clinical assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 1024
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                return f'{{"error": "OpenRouter error: {response.status_code}"}}'
                
        except Exception as e:
            logger.error(f"OpenRouter fallback failed: {e}")
            return f'{{"error": "Fallback failed: {str(e)}"}}'
    
    @staticmethod
    def get_available_models() -> dict:
        """Get status of all available models."""
        models = OllamaService.get_available_models()
        
        status = {
            "available": models,
            "routing_map": {
                task.value: ModelRouter.get_model_for_task(task)
                for task in TaskType
            },
            "config": {
                model: ModelRouter.get_config_for_model(model)
                for model in models
            }
        }
        
        return status
