import requests
import os
import json
from typing import Optional, Dict, Any
import logging
from app.services.ollama_service import OllamaService
from app.services.model_router import ModelRouter, TaskType
from app.prompts.system_prompts import HELIX_CORE_PROMPT, SYSTEM_CONTEXT

logger = logging.getLogger(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


def call_llm(prompt: str, model: str = "auto", use_ollama: bool = True) -> str:
    """
    Call LLM with smart routing.
    
    Args:
        prompt: The prompt to send to the model
        model: The model to use ("auto" for smart routing)
        use_ollama: Prefer Ollama if available
    
    Returns:
        The model's response text
    """
    
    if use_ollama and OllamaService.is_available():
        # Use local Ollama model
        if model == "auto":
            model = ModelRouter.get_model_for_task(TaskType.DEEP_REASONING)
        
        logger.info(f"Using Ollama model: {model}")
        return OllamaService.call_model(
            model=model,
            prompt=prompt,
            system=SYSTEM_CONTEXT,
            temperature=0.3,
            timeout=60
        )
    else:
        # Fallback to OpenRouter
        logger.info("Using OpenRouter API")
        return _call_openrouter(prompt)


def call_llm_with_routing(
    task_type: TaskType,
    prompt: str,
    system_prompt: Optional[str] = None
) -> str:
    """
    Call LLM with intelligent task routing.
    
    Args:
        task_type: Type of task
        prompt: The prompt
        system_prompt: Optional system prompt
    
    Returns:
        Model response
    """
    
    if system_prompt is None:
        system_prompt = SYSTEM_CONTEXT
    
    # Use model router for optimal model selection
    return ModelRouter.call_task(
        task_type=task_type,
        prompt=prompt,
        system_prompt=system_prompt,
        fallback_to_openrouter=True
    )


def call_gemma(prompt: str, context: Optional[str] = None) -> str:
    """Call Gemma reasoning model directly."""
    if not OllamaService.is_available():
        logger.warning("Ollama not available, using fallback")
        return _call_openrouter(prompt)
    
    return OllamaService.call_model(
        model="gemma:4b",
        prompt=prompt,
        system=HELIX_CORE_PROMPT,
        temperature=0.2,
        context=context,
        timeout=120
    )


def call_nemotron(prompt: str) -> str:
    """Call Nemotron routing model directly."""
    if not OllamaService.is_available():
        logger.warning("Ollama not available, using fallback")
        return _call_openrouter(prompt)
    
    return OllamaService.call_model(
        model="nemotron:4b",
        prompt=prompt,
        system=SYSTEM_CONTEXT,
        temperature=0.3,
        timeout=30
    )


def stream_llm(task_type: TaskType, prompt: str, system_prompt: Optional[str] = None):
    """
    Stream LLM response for real-time UI updates.
    
    Yields response chunks as they arrive.
    """
    if system_prompt is None:
        system_prompt = SYSTEM_CONTEXT
    
    if not OllamaService.is_available():
        logger.warning("Ollama not available for streaming")
        yield '{"error": "Streaming not available"}'
        return
    
    model = ModelRouter.get_model_for_task(task_type)
    
    try:
        for chunk in OllamaService.call_model_streaming(
            model=model,
            prompt=prompt,
            system=system_prompt,
            temperature=0.3
        ):
            yield chunk
    except Exception as e:
        logger.error(f"Streaming error: {e}")
        yield f'{{"error": "{str(e)}"}}'


def _call_openrouter(prompt: str) -> str:
    """Fallback to OpenRouter API."""
    try:
        if not OPENROUTER_API_KEY:
            return '{"error": "OpenRouter API key not configured"}'
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "qwen/qwen3-32b",
                "messages": [
                    {
                        "role": "system",
                        "content": SYSTEM_CONTEXT
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
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
        return f'{{"error": "{str(e)}"}}'


def structured_llm_call(prompt: str, task_type: TaskType = TaskType.DEEP_REASONING) -> dict:
    """
    Call LLM and ensure JSON structured output.
    
    Args:
        prompt: The prompt
        task_type: Type of task for routing
    
    Returns:
        Parsed JSON response
    """
    response = call_llm_with_routing(task_type, prompt)
    
    # Parse response
    parsed = OllamaService.parse_json_response(response)
    
    # Validate structure
    if "error" in parsed and "insufficient_data" not in parsed.get("error", ""):
        # Try to extract JSON from error response
        import re
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except:
                pass
    
    return parsed


def get_model_status() -> Dict[str, Any]:
    """Get current model status and availability."""
    return {
        "ollama_available": OllamaService.is_available(),
        "models": OllamaService.get_available_models(),
        "routing": ModelRouter.get_available_models()
    }

