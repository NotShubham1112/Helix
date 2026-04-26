"""
Model Configuration

Stores exact model names that match `ollama list` output.
These MUST match exactly or warmup will fail.
"""

# Model mappings - these are the EXACT names from ollama list
MODELS = {
    "reasoning": "gemma4:e2b",
    "router": "nemotron-3-nano:4b",
    "coding": "codestral:latest",
    "ocr": "glm-ocr:bf16",
}

# Models to warmup on startup (memory-safe for RTX 3050)
WARMUP_MODELS = [
    "nemotron-3-nano:4b",
    "gemma4:e2b",
]

# Model-specific settings
MODEL_SETTINGS = {
    "nemotron-3-nano:4b": {
        "temperature": 0.3,
        "timeout": 30,
    },
    "gemma4:e2b": {
        "temperature": 0.3,
        "timeout": 30,
    },
    "codestral:latest": {
        "temperature": 0.1,
        "timeout": 60,
    },
    "glm-ocr:bf16": {
        "temperature": 0.1,
        "timeout": 45,
    },
}

# Ollama configuration
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MAX_RETRIES = 20
OLLAMA_RETRY_DELAY = 1  # seconds
WARMUP_DELAY = 2  # seconds between model warmups (memory safety)
WARMUP_TIMEOUT = 30  # seconds per warmup
WARMUP_PROMPT = "Respond with OK"
