# 🧬 Helix Backend - Production-Grade Clinical AI System

A modular, multimodal clinical intelligence backend built with FastAPI, featuring AI orchestration, medical reasoning, and RAG-based knowledge grounding.

## 🏗️ Architecture

```
User Request
    ↓
[ FastAPI Router ]
    ↓
[ Intent Classifier - Nemotron ]
    ↓
[ Service Orchestrator ]
    ├── Lab Report → OCR → Analysis
    ├── Drug Query → Drug Service → Interactions
    ├── Symptoms → Reasoning → RAG Context
    └── General Chat → Health Analysis
    ↓
[ Structured Response ]
```

## 📁 Project Structure

```
helix-backend/
├── app/
│   ├── main.py                 # FastAPI entry point
│   ├── routes/
│   │   ├── upload.py          # File upload & processing
│   │   ├── chat.py            # Chat interface
│   │   └── analyze.py         # Medical analysis endpoints
│   ├── services/
│   │   ├── llm_service.py     # LLM calls (OpenRouter)
│   │   ├── ocr_service.py     # OCR & lab value extraction
│   │   ├── reasoning_service.py # Clinical reasoning
│   │   ├── rag_service.py     # RAG & retrieval
│   │   ├── drug_service.py    # Drug info & interactions
│   │   ├── router_service.py  # Intent classification
│   │   └── orchestrator.py    # Request routing
│   ├── models/
│   │   └── schemas.py         # Pydantic models
│   ├── prompts/
│   │   └── clinical_prompt.py # LLM prompts
│   └── utils/
│       └── helpers.py         # Utility functions
├── vector_db/                 # Vector database storage
├── requirements.txt           # Python dependencies
└── .env                       # Environment variables
```

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- pip or poetry
- OpenRouter API key (for LLM access)

### 1. Install Dependencies

```bash
cd helix-backend
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env` and set your variables:

```bash
cp .env .env.local
```

Edit `.env.local`:
```
OPENROUTER_API_KEY=your_key_here
DATABASE_URL=postgresql://user:pass@localhost/helix
```

### 3. Run Backend

```bash
# Development with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Backend will be available at: `http://localhost:8000`

### 4. API Documentation

Interactive API docs:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🔌 API Endpoints

### Upload Medical Reports
```bash
POST /api/upload/
- Upload PDF, image, or text medical reports
- Extracts data via OCR
- Returns structured lab values

POST /api/upload/analyze
- Upload and immediately analyze
- Returns full clinical analysis
```

### Chat Interface
```bash
POST /api/chat/
- Query the clinical AI
- Intent-based routing
- Structured responses

POST /api/chat/stream
- Streaming responses for UI
```

### Analysis Services
```bash
POST /api/analyze/
- Full health analysis
- RAG-grounded reasoning
- Confidence scores

POST /api/analyze/labs
- Lab test analysis
- Abnormality detection

POST /api/analyze/drugs
- Drug information
- Interaction checking

POST /api/analyze/full-assessment
- Comprehensive health assessment
```

## 🧠 Core Services

### 1. Intent Router (Nemotron)
Classifies user input into categories:
- `lab_report`: Lab test results
- `prescription`: Drug queries
- `imaging`: X-ray/CT/ultrasound
- `symptom_query`: Patient symptoms
- `general_chat`: General questions

### 2. LLM Service
- **Primary**: OpenRouter (Qwen 3 32B)
- **Fallback**: Local Gemma (future)
- Temperature: 0.3 (clinical accuracy)
- Max tokens: 1024

### 3. Reasoning Engine
- Clinical decision support
- Multi-step reasoning
- Hallucination detection
- Confidence scoring

### 4. RAG Layer
- Medical literature grounding
- Vector similarity search (FAISS/Chroma)
- Context augmentation
- Cites sources

### 5. Drug Service
- Drug database lookup
- Interaction detection
- Contraindication checking
- Side effect information

## 🔐 Safety & Guardrails

### Hallucination Detection
Forbidden patterns:
- "you have diagnosed"
- "confirmed disease"
- "guaranteed"
- "100% certain"

### Prompt Engineering
- System role: Clinical assistant
- Low temperature (0.3)
- Structured output format
- Confidence scores

### Output Validation
- JSON schema validation
- Pydantic models
- Type checking
- Field verification

## 📊 Request/Response Examples

### Lab Analysis
**Request:**
```json
{
  "data": {
    "hemoglobin": "10 g/dL",
    "glucose": "140 mg/dL",
    "creatinine": "1.2 mg/dL"
  }
}
```

**Response:**
```json
{
  "summary": "Elevated glucose levels detected",
  "abnormalities": ["Glucose: 140 mg/dL (High)"],
  "risks": [
    {
      "condition": "Type 2 Diabetes",
      "probability": "Moderate",
      "reason": "Elevated fasting glucose"
    }
  ],
  "recommendations": [
    {
      "action": "Consult physician",
      "urgency": "Medium"
    }
  ],
  "confidence": 0.82
}
```

### Chat Query
**Request:**
```json
{
  "message": "What does elevated hemoglobin mean?"
}
```

**Response:**
```json
{
  "reply": "Elevated hemoglobin may indicate dehydration, high altitude, or certain blood disorders...",
  "intent": "symptom_query",
  "confidence": 0.87
}
```

## 🛠️ Development

### Adding New Services
1. Create service file in `app/services/`
2. Define functions with type hints
3. Add to orchestrator
4. Create routes in `app/routes/`

### Testing
```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/ -v
```

### Environment Variables
```
# Required
OPENROUTER_API_KEY=sk-...

# Optional
DATABASE_URL=postgresql://...
VECTOR_DB_PATH=./vector_db
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

## 📦 Dependencies

**Core:**
- FastAPI: Web framework
- Uvicorn: ASGI server
- Pydantic: Data validation

**AI/ML:**
- OpenAI (for OpenRouter)
- NumPy, Pandas: Data processing
- FAISS: Vector search

**Database:**
- SQLAlchemy: ORM
- psycopg2: PostgreSQL driver

**Utilities:**
- python-dotenv: Environment management
- requests: HTTP client

## 🐳 Docker Support (Future)

```bash
docker build -t helix-backend .
docker run -p 8000:8000 --env-file .env helix-backend
```

## 📈 Production Checklist

- [ ] Set `OPENROUTER_API_KEY`
- [ ] Configure `DATABASE_URL`
- [ ] Enable authentication (JWT)
- [ ] Set `CORS_ORIGINS` to frontend domain
- [ ] Enable HTTPS
- [ ] Set up logging
- [ ] Configure rate limiting
- [ ] Add request/response validation
- [ ] Monitor LLM costs
- [ ] Track hallucination rate
- [ ] Set up error tracking (Sentry)
- [ ] Regular backups

## 🤝 Contributing

1. Create feature branch
2. Add tests
3. Update prompts if needed
4. Submit pull request

## 📝 License

MIT

## 🆘 Support

For issues or questions, check:
- `/docs` - API documentation
- `app/prompts/` - LLM prompts
- `app/services/` - Service implementations
- `app/utils/helpers.py` - Common utilities
