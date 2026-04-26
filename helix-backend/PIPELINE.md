# HELIX Report Processing Pipeline

Complete backend for healthcare SaaS system processing medical documents with local LLMs and RAG.

## 🏗️ Architecture

```
USER UPLOADS FILE
        ↓
    [UPLOAD API]
        ↓
    [OCR SERVICE] → Extract text from file
        ↓
    [PARSER SERVICE] → Normalize lab values
        ↓
    [SUPABASE] → Store parsed data
        ↓
    [LLM SERVICE] → Generate report (Ollama)
        ↓
    [RAG SERVICE] → Store in vector memory
        ↓
    [RESPONSE] → Return report_id
        ↓
    USER ASKS QUESTION
        ↓
    [CHAT API]
        ↓
    [RAG SERVICE] → Retrieve user context
        ↓
    [LLM SERVICE] → Generate answer
        ↓
    [SUPABASE] → Store conversation
        ↓
    [RESPONSE] → Return answer
```

## 📁 Project Structure

```
app/
  routes/
    upload.py          # File upload & processing pipeline
    report.py          # Report retrieval & management
    chat.py            # Chat over reports
    
  services/
    ocr_service.py     # Text extraction (placeholder)
    parser_service.py  # Lab value normalization
    rag_service.py     # FAISS vector memory
    llm_service.py     # Ollama integration
    report_service.py  # Report generation
    
  db/
    supabase_client.py # Database operations
    init_db.py         # Schema initialization
    
  dependencies/
    auth.py            # JWT verification
    
  models/
    schemas.py         # Request/response models
    
  main.py             # FastAPI app & routing

sql/
  migrations/
    02_helix_reports.sql  # Database schema

requirements-complete.txt  # Dependencies
```

## 🚀 Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements-complete.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with:
- `SUPABASE_URL` & `SUPABASE_KEY` from Supabase dashboard
- `SUPABASE_JWT_SECRET` for JWT verification
- `OLLAMA_URL` pointing to local Ollama instance

### 3. Initialize Database

```bash
# Execute SQL from sql/migrations/02_helix_reports.sql in Supabase SQL Editor
# OR run initialization script:
python -m app.db.init_db
```

### 4. Start Ollama

```bash
# Terminal 1: Start Ollama service
ollama serve

# Terminal 2: Pull models
ollama pull gemma:4b
ollama pull nemotron:4b
```

### 5. Start Backend

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📊 API Endpoints

### Upload & Process

**POST** `/api/upload/`
- Accept medical document (PDF, image)
- Extract → Parse → Generate report
- Return report_id

```bash
curl -X POST "http://localhost:8000/api/upload/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@lab_report.pdf"
```

Response:
```json
{
  "status": "success",
  "report_id": "uuid-here",
  "message": "Report generated successfully",
  "file_name": "lab_report.pdf",
  "processed_at": "2024-01-15T10:30:00Z"
}
```

### Get Report Details

**GET** `/api/report/{report_id}`
- Get formatted report with analysis

```bash
curl -X GET "http://localhost:8000/api/report/uuid-here" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

Response:
```json
{
  "status": "success",
  "report": {
    "id": "uuid-here",
    "summary": "Lab results show elevated glucose...",
    "abnormalities": ["High glucose: 140 mg/dL"],
    "risk_assessment": ["Indication of possible diabetes risk"],
    "recommendations": ["Consult healthcare provider"],
    "confidence": 0.85
  }
}
```

### Chat Over Report

**POST** `/api/chat/`
- Ask questions about report
- Uses RAG to retrieve context
- Ollama generates answer

```bash
curl -X POST "http://localhost:8000/api/chat/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What does the glucose level mean?",
    "report_id": "uuid-here"
  }'
```

Response:
```json
{
  "message_id": "msg-uuid",
  "reply": "Your glucose level of 140 mg/dL is elevated...",
  "confidence": 0.85,
  "context_used": 3
}
```

### List Reports

**GET** `/api/upload/`
- Get all reports for authenticated user

```bash
curl -X GET "http://localhost:8000/api/upload/?limit=50" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## 🔐 Security Features

### User Isolation
- Every request uses `user_id` from JWT token
- Database queries filtered by `user_id` (RLS enabled)
- FAISS indices per user (separate directories)
- Supabase Row Level Security (RLS) enforced

### Safety Rules
- NEVER output diagnosis ("you have X disease")
- ALWAYS use cautious language ("indication of risk")
- Return `insufficient_data` error if needed
- Validate reports for dangerous keywords

### Authentication
- JWT token verification on all endpoints
- Token extracted from Authorization header
- Claims validation (sub/user_id required)

## 🧠 AI Pipeline Details

### OCR Service
- Input: File bytes (PDF, image)
- Placeholder returns mock lab values
- Production: Integrate GLM-OCR or similar

Mock output:
```python
{
    "glucose": "140 mg/dL",
    "hemoglobin": "10 g/dL",
    "creatinine": "1.2 mg/dL",
    ...
}
```

### Parser Service
- Normalize values to standard units
- Compare against reference ranges
- Detect abnormal results
- Calculate patterns (diabetes, anemia, etc.)

Output:
```python
{
    "values": {
        "glucose": {
            "value": 140,
            "unit": "mg/dL",
            "status": "high",
            "normal_range": "70-100 mg/dL"
        }
    },
    "abnormalities": [...],
    "summary": {...}
}
```

### RAG Service (FAISS)
- Store report text in FAISS vector index
- Per-user isolation (separate indices)
- Retrieve top-k similar documents for chat
- Uses sentence-transformers for embeddings

Usage:
```python
RAGService.add_report_to_memory(user_id, report_id, text)
context = RAGService.retrieve_for_chat(user_id, question)
```

### LLM Service (Ollama)
- Primary: `gemma:4b` (report generation)
- Secondary: `nemotron:4b` (routing)
- System prompt ensures safety
- Temperature 0.3 for consistency

Request to Ollama:
```
POST http://localhost:11434/api/generate
{
    "model": "gemma:4b",
    "prompt": "...",
    "system": "You are HELIX...",
    "temperature": 0.3,
    "stream": false
}
```

### Report Service
- Builds LLM prompt with patient data
- Generates structured JSON report
- Validates for safety compliance
- Returns strict structure:

```json
{
    "summary": "2-3 sentence overview",
    "abnormalities": ["Finding 1", "Finding 2"],
    "risk_assessment": ["Risk 1", "Risk 2"],
    "recommendations": ["Action 1", "Action 2"],
    "confidence": 0.85
}
```

## 📚 Database Schema

### `reports` table
- `id` (uuid): Report identifier
- `user_id` (uuid): User identifier
- `file_name` (text): Original filename
- `file_url` (text): Supabase storage URL
- `parsed_data` (jsonb): Normalized lab values
- `analysis_result` (jsonb): LLM-generated report
- `status` (text): processing | completed | failed
- `created_at`, `updated_at` (timestamp)

### `analysis` table
- `id` (uuid): Analysis identifier
- `report_id` (uuid): Associated report
- `user_id` (uuid): User identifier
- `result` (jsonb): Full analysis
- `created_at` (timestamp)

### `chat_messages` table
- `id` (uuid): Message identifier
- `report_id` (uuid): Associated report
- `user_id` (uuid): User identifier
- `message` (text): User question
- `response` (text): AI response
- `metadata` (jsonb): Context info
- `created_at` (timestamp)

### RLS Policies
- All tables require `auth.uid()` = `user_id`
- Users can only see their own data
- Row-level security enforced by Supabase

## 🧪 Testing

### Upload test
```bash
curl -X POST http://localhost:8000/api/upload/ \
  -H "Authorization: Bearer test-token" \
  -F "file=@test.pdf"
```

### Chat test
```bash
curl -X POST http://localhost:8000/api/chat/ \
  -H "Authorization: Bearer test-token" \
  -H "Content-Type: application/json" \
  -d '{"message":"What is my glucose?","report_id":"abc123"}'
```

### Health check
```bash
curl http://localhost:8000/health
```

## ⚙️ Configuration

Key environment variables:
```env
SUPABASE_URL=https://...supabase.co
SUPABASE_KEY=eyJ...
SUPABASE_JWT_SECRET=your-secret
OLLAMA_URL=http://localhost:11434
OLLAMA_PRIMARY_MODEL=gemma:4b
FAISS_INDEX_DIR=./faiss_indices
ENVIRONMENT=development
```

## 🚀 Production Deployment

1. **Use production Supabase project**
   - Update SUPABASE_URL, SUPABASE_KEY
   - Enable HTTPS for API

2. **Configure Ollama**
   - Deploy on dedicated GPU machine
   - Use load balancer for high availability

3. **Enable HIPAA mode**
   - `HIPAA_MODE=true`
   - `ENCRYPT_PII=true`
   - Configure data retention

4. **Monitor & Log**
   - Configure Sentry for error tracking
   - Enable Application Insights
   - Monitor Ollama GPU usage

5. **Scale RAG**
   - Use distributed FAISS (if needed)
   - Or migrate to cloud vector DB (Pinecone, Weaviate)

## 📝 Safety & Compliance

### Medical Safety
- Never diagnose ("you have diabetes")
- Use cautious language ("indication of risk")
- Return error if insufficient data
- Encourage doctor consultation

### Data Privacy
- HIPAA mode encryption
- Row-level security (RLS)
- User isolation at all levels
- GDPR-compliant data deletion

### Audit Trail
- All queries logged
- Chat history preserved
- Timestamps on all records
- User isolation enforced

## 🔧 Troubleshooting

### Ollama connection error
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Verify model is installed
ollama list
```

### JWT token issues
- Verify token in .env matches Supabase JWT secret
- Check token expiration
- Confirm Authorization header format: `Bearer <token>`

### FAISS index errors
- Check `FAISS_INDEX_DIR` permissions
- Verify disk space available
- Clear corrupted indices if needed

### Database errors
- Verify Supabase connection
- Check RLS policies enabled
- Confirm tables created (run migration)
- Verify admin key used for initialization

## 📖 API Documentation

Full OpenAPI documentation:
```
http://localhost:8000/docs
```

Interactive API explorer (ReDoc):
```
http://localhost:8000/redoc
```

## 📄 License

Proprietary - HELIX Healthcare System
