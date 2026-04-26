# HELIX Backend - Quick Start Guide

Get the complete healthcare report processing pipeline running in 10 minutes.

## 📋 Prerequisites

- Python 3.10+
- Ollama installed (for local LLMs)
- Supabase account (free tier works)
- Git

## 🚀 Setup (10 minutes)

### Step 1: Clone & Navigate (1 min)
```bash
cd helix-backend
```

### Step 2: Create Virtual Environment (1 min)
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies (2 min)
```bash
pip install -r requirements-complete.txt
```

### Step 4: Configure Environment (2 min)
```bash
cp .env.example .env
```

Edit `.env`:
```env
# Supabase (get from dashboard)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_JWT_SECRET=your-jwt-secret

# Ollama (local LLM)
OLLAMA_URL=http://localhost:11434
OLLAMA_PRIMARY_MODEL=gemma:4b
OLLAMA_ROUTING_MODEL=nemotron:4b
```

### Step 5: Database Setup (2 min)
1. Go to Supabase Dashboard → SQL Editor
2. Copy content from `sql/migrations/02_helix_reports.sql`
3. Paste & execute in SQL editor
4. Verify tables created in Tables panel

### Step 6: Start Services (2 min)

**Terminal 1 - Ollama:**
```bash
ollama serve
```

**Terminal 2 - Pull Models:**
```bash
ollama pull gemma:4b
ollama pull nemotron:4b
```

**Terminal 3 - Backend:**
```bash
source venv/bin/activate  # if not already
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## ✅ Verify Setup

### Health Check
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "healthy", "service": "HELIX Medical AI", "version": "1.0.0"}
```

### API Documentation
Open in browser:
```
http://localhost:8000/docs
```

## 🧪 Test API (with JWT Token)

### 1. Get a Test JWT Token
First, get a test token from your Supabase project:
```bash
# In Supabase console, create a test user or use JWT debugger
# Copy the token
export JWT_TOKEN="your-jwt-token-here"
```

### 2. Upload & Process Document
```bash
curl -X POST "http://localhost:8000/api/upload/" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -F "file=@test_report.pdf"
```

Response:
```json
{
  "status": "success",
  "report_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Report generated successfully",
  "file_name": "test_report.pdf",
  "processed_at": "2024-01-15T10:30:00Z"
}
```

### 3. Get Report Details
```bash
curl -X GET "http://localhost:8000/api/report/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

### 4. Chat About Report
```bash
curl -X POST "http://localhost:8000/api/chat/" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What does my glucose level indicate?",
    "report_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

## 📁 Project Structure

```
helix-backend/
├── app/
│   ├── routes/           # API endpoints
│   │   ├── upload.py     # File upload pipeline
│   │   ├── report.py     # Report management
│   │   └── chat.py       # Chat interface
│   ├── services/         # Business logic
│   │   ├── ocr_service.py       # Text extraction
│   │   ├── parser_service.py    # Value normalization
│   │   ├── rag_service.py       # Vector memory (FAISS)
│   │   ├── llm_service.py       # LLM calls (Ollama)
│   │   └── report_service.py    # Report generation
│   ├── db/               # Database
│   │   ├── supabase_client.py   # DB operations
│   │   └── init_db.py           # Schema init
│   ├── dependencies/     # Middlewares
│   │   └── auth.py       # JWT verification
│   ├── models/
│   │   └── schemas.py    # Type definitions
│   └── main.py           # FastAPI app
├── sql/migrations/       # Database schema
├── PIPELINE.md           # Architecture & usage
├── IMPLEMENTATION_SUMMARY.md
├── requirements-complete.txt
├── .env.example          # Configuration template
└── README.md             # This file
```

## 🔑 Key Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/upload/` | Upload & process document |
| GET | `/api/upload/` | List user reports |
| GET | `/api/report/{id}` | Get report details |
| DELETE | `/api/report/{id}` | Delete report |
| POST | `/api/chat/` | Chat about report |
| GET | `/api/chat/{id}/history` | Get conversation history |

All endpoints require JWT token in `Authorization: Bearer <token>` header.

## 📚 Documentation

- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **ReDoc**: http://localhost:8000/redoc
- **Pipeline Guide**: See `PIPELINE.md`
- **Implementation**: See `IMPLEMENTATION_SUMMARY.md`

## 🐛 Troubleshooting

### Ollama Not Connecting
```bash
# Check if running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve

# Pull models if missing
ollama pull gemma:4b
ollama pull nemotron:4b
```

### Database Connection Error
```bash
# Verify .env variables
echo $SUPABASE_URL
echo $SUPABASE_KEY

# Check connection
python -c "from app.db.supabase_client import get_supabase; print(get_supabase().is_available())"
```

### JWT Token Issues
```bash
# Verify token format
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/health

# Check token secret in .env matches Supabase
# SUPABASE_JWT_SECRET must match Supabase settings
```

### FAISS Index Permission Error
```bash
# Check directory exists and is writable
mkdir -p ./faiss_indices
chmod 755 ./faiss_indices
```

## 🔄 Common Tasks

### Add a New Endpoint
1. Create route in `app/routes/`
2. Import in `app/main.py`
3. Add to router list
4. Access at `/api/{prefix}/{path}`

### Integrate New OCR
1. Edit `app/services/ocr_service.py`
2. Implement `extract_text()` function
3. Return dict with lab values
4. System handles normalization

### Switch LLM Models
Edit `.env`:
```env
OLLAMA_PRIMARY_MODEL=mistral:7b
OLLAMA_ROUTING_MODEL=neural-chat:7b
```

### Change Database
1. Update `SUPABASE_URL` & `SUPABASE_KEY`
2. Run migrations in new database
3. Restart backend

## 📊 Architecture Overview

```
┌─────────────┐
│   USER      │
└──────┬──────┘
       │
       ▼ Upload File
   ┌─────────────────────────────────┐
   │  UPLOAD API (/api/upload)       │
   └─┬──────────────────────────────┘
     │
     ├─► OCR Service (extract_text)
     ├─► Parser Service (normalize)
     ├─► Supabase Storage (upload file)
     ├─► DB (store report)
     ├─► LLM Service → Ollama (generate)
     └─► RAG Service → FAISS (store memory)
             │
             ▼ Return report_id
   ┌─────────────────────────────────┐
   │   USER (with report_id)         │
   └──────┬──────────────────────────┘
          │
          ▼ Ask Question
   ┌─────────────────────────────────┐
   │   CHAT API (/api/chat)          │
   └─┬──────────────────────────────┘
     │
     ├─► Get Report from DB
     ├─► RAG Service → FAISS (retrieve)
     ├─► Build Context
     ├─► LLM Service → Ollama (answer)
     └─► Store Conversation
             │
             ▼ Return Response
   ┌─────────────────────────────────┐
   │   USER (with answer)            │
   └─────────────────────────────────┘
```

## 🚀 Next Steps

1. ✅ Complete setup above
2. 📖 Read `PIPELINE.md` for detailed architecture
3. 🧪 Test endpoints with provided curl commands
4. 🔧 Customize OCR, LLM prompts as needed
5. 📦 Deploy to production (see PIPELINE.md)

## 📞 Support

Issues? Check:
1. `.env` configuration (all variables set)
2. Ollama running (curl http://localhost:11434)
3. Supabase connection (tables created)
4. JWT token format (Bearer <token>)
5. Logs in terminal for error details

## 📝 Notes

- All user data is isolated by user_id from JWT
- Reports are stored in Supabase + FAISS indices
- Chat history persisted in database
- Ollama models run locally (no cloud API calls)
- HIPAA mode available in .env

---

**Ready to go!** 🎉

Start with: `uvicorn app.main:app --reload`

Then open: `http://localhost:8000/docs`
