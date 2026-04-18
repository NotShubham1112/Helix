# 🚀 Ollama Setup Guide for HELIX

## Prerequisites

- **RTX 3050 GPU** (or any NVIDIA GPU with CUDA support)
- **Windows/macOS/Linux**
- **Python 3.10+**
- **FastAPI backend configured**

---

## Step 1: Install Ollama

### Windows

1. Download from [https://ollama.ai](https://ollama.ai)
2. Run installer
3. Ollama will run as a background service

Check if running:
```powershell
curl http://localhost:11434/api/tags
```

### macOS

```bash
brew install ollama
```

Start Ollama:
```bash
ollama serve
```

### Linux

```bash
curl https://ollama.ai/install.sh | sh

# Start service
systemctl start ollama
```

---

## Step 2: Pull Required Models

The backend auto-pulls models on startup, but you can pre-pull them:

### Pull Nemotron (Router - Fast)

```bash
ollama pull nemotron:4b
```

**Size:** ~2.6 GB
**Use:** Intent classification, fast responses
**Speed:** ~100-200ms per inference

### Pull Gemma (Reasoning - Accurate)

```bash
ollama pull gemma:4b
```

**Size:** ~2.5 GB
**Use:** Deep analysis, clinical reasoning
**Speed:** ~500-1000ms per inference

### Total Space Required
- ~5.5 GB for both models
- ~2 GB for VRAM when loaded

---

## Step 3: Verify Models

```bash
# List downloaded models
ollama list

# Output:
# NAME           ID              SIZE      MODIFIED
# gemma:4b       4b82cc662ffb    2.5 GB    2 minutes ago
# nemotron:4b    abc123def456    2.6 GB    1 minute ago
```

---

## Step 4: Test Local Models

### Test Nemotron
```bash
ollama run nemotron:4b "Hello, how are you?"
```

### Test Gemma
```bash
ollama run gemma:4b "Explain hemoglobin levels"
```

Both should respond within a few seconds.

---

## Step 5: Install Backend Dependencies

```bash
cd D:\Parth\Helix\helix-backend

pip install -r requirements.txt
```

Add these to `requirements.txt` if not present:
```
requests>=2.31.0
ollama>=0.1.0
```

---

## Step 6: Configure Environment

Create or update `.env`:

```env
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TIMEOUT=60

# Fallback to OpenRouter if needed
OPENROUTER_API_KEY=sk-...  # Optional

# Logging
LOG_LEVEL=INFO
```

---

## Step 7: Start Backend

The backend will auto-initialize Ollama and warmup models:

```bash
cd D:\Parth\Helix\helix-backend

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Expected Output

```
🚀 Starting Ollama service...
✓ Ollama is already running
🔍 Checking available models...
Found models: ['gemma:4b', 'nemotron:4b']
📦 Ensuring models are available...
✓ Model gemma:4b available
✓ Model nemotron:4b available
🔥 Warming up models...
Warming up gemma:4b...
Warming up nemotron:4b...
✓ gemma:4b ready
✓ nemotron:4b ready
🏥 Running health checks...
Health Status: healthy

============================================
✓ HELIX Backend Ready!
============================================
```

---

## Step 8: Verify System Status

```bash
# Check overall health
curl http://localhost:8000/health

# Check model status
curl http://localhost:8000/status
```

**Expected response:**
```json
{
  "ollama": true,
  "models": {
    "gemma:4b": true,
    "nemotron:4b": true
  },
  "status": "healthy"
}
```

---

## Step 9: Test Lab Analysis

```bash
curl -X POST http://localhost:8000/api/analyze/labs \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "hemoglobin": "10 g/dL",
      "glucose": "140 mg/dL",
      "creatinine": "1.5 mg/dL"
    }
  }'
```

**Expected response:**
```json
{
  "validation": {
    "data": {...},
    "abnormalities": [
      {
        "test": "hemoglobin",
        "value": "10 g/dL",
        "status": "abnormal"
      }
    ]
  },
  "analysis": {
    "summary": "Elevated glucose and low hemoglobin detected...",
    "risks": [...],
    "confidence": 0.82
  }
}
```

---

## 🔧 Troubleshooting

### Ollama Not Starting

```powershell
# Windows - Check if service is running
Get-Service | grep -i ollama

# Start service manually
net start ollama

# Or restart
net stop ollama
net start ollama
```

### Models Not Downloading

```bash
# Manually pull
ollama pull gemma:4b --verbose

# Check disk space
df -h  # Linux/macOS
dir C:  # Windows
```

### Out of VRAM

**Symptoms:** "CUDA out of memory" errors

**Solutions:**
1. Reduce batch size in model calls
2. Use smaller models (e.g., 2b instead of 4b)
3. Clear VRAM: `nvidia-smi --query-compute-apps=pid --format=csv,noheader | xargs kill -9`

### Slow Responses

**Check:**
```bash
# Monitor GPU usage
nvidia-smi -l 1

# Expected: ~3-4GB VRAM per model when loaded
```

**Optimize:**
- Ensure models are warmed up (check backend startup)
- Close other GPU applications
- Ensure good internet for first model load

### Backend Timeout

```bash
# Increase timeout in .env
OLLAMA_TIMEOUT=120
```

Or in code:
```python
OllamaService.call_model(..., timeout=120)
```

---

## 📊 Performance Tuning

### For RTX 3050

**Recommended settings:**
```python
# config.py
MODELS_TO_LOAD = [
    "nemotron:4b",  # 2.6 GB
    "gemma:4b",     # 2.5 GB
]

# RTX 3050 can handle both ~5GB
# Total VRAM: 8GB DDR6
```

### Expected Latency

| Task | Model | Latency |
|------|-------|---------|
| Intent Classification | Nemotron 4b | 100-200ms |
| Quick Response | Nemotron 4b | 200-400ms |
| Lab Analysis | Gemma 4b | 800-1500ms |
| Full Assessment | Gemma 4b | 2000-3000ms |

---

## 🔄 Updating Models

### Pull Latest Version

```bash
# Pull latest
ollama pull gemma:latest

# Or specific version
ollama pull gemma:4b
```

### Remove Old Models

```bash
ollama rm gemma:7b
ollama rm nemotron:7b
```

---

## 📋 Checklist

- ✅ Ollama installed and running
- ✅ Models downloaded (gemma:4b, nemotron:4b)
- ✅ Backend dependencies installed
- ✅ `.env` configured
- ✅ Backend starts without errors
- ✅ Models warmed up on startup
- ✅ Health check responds with `healthy`
- ✅ Lab analysis returns results
- ✅ Latency acceptable for your use case

---

## 🆘 Getting Help

**Ollama Issues:**
- Check: https://github.com/ollama/ollama/issues
- Docs: https://github.com/ollama/ollama

**HELIX Issues:**
- Check logs: `helix-backend/logs/`
- Test endpoint: `curl http://localhost:8000/health`
- Verify models: `ollama list`

---

## 🎯 Next: Start Frontend

Once backend is healthy:

```bash
cd D:\Parth\Helix\helix

npm install
npm run dev
```

Frontend: http://localhost:3000
Backend: http://localhost:8000
