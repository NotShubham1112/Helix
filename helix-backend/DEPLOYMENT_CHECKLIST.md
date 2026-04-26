# HELIX Backend - Deployment Checklist

Complete checklist for deploying the healthcare report processing pipeline.

## ✅ Pre-Deployment Checklist

### Code Quality
- [ ] All Python files follow PEP 8 style
- [ ] Type hints added to all functions
- [ ] Error handling in place
- [ ] Logging configured
- [ ] No hardcoded secrets
- [ ] All imports resolvable

### Dependencies
- [ ] `requirements-complete.txt` updated
- [ ] All packages available on PyPI
- [ ] Python 3.10+ confirmed
- [ ] Virtual environment tested
- [ ] `pip install -r requirements-complete.txt` succeeds

### Configuration
- [ ] `.env.example` complete and documented
- [ ] All required env variables listed
- [ ] `.env` created with actual values
- [ ] JWT secret configured
- [ ] Supabase credentials verified
- [ ] Ollama URL accessible

### Database
- [ ] Supabase project created
- [ ] SQL migrations executed
- [ ] Tables created and verified
- [ ] RLS policies enabled
- [ ] Indexes created
- [ ] Storage bucket created
- [ ] Schema matches `02_helix_reports.sql`

### LLM Setup
- [ ] Ollama installed
- [ ] `gemma:4b` model pulled
- [ ] `nemotron:4b` model pulled
- [ ] `ollama serve` tested
- [ ] API endpoint responds
- [ ] Models listed with `ollama list`

### Authentication
- [ ] Supabase JWT secret obtained
- [ ] JWT algorithm configured (HS256)
- [ ] Test token generated
- [ ] Token verification tested
- [ ] User isolation verified

### API Testing
- [ ] Health check endpoint works
- [ ] Upload endpoint accepts files
- [ ] OCR service returns data
- [ ] Parser normalizes values
- [ ] LLM generates reports
- [ ] RAG stores and retrieves
- [ ] Chat endpoint works
- [ ] All endpoints require auth

### Security
- [ ] No diagnosis output in reports
- [ ] Safety keywords validated
- [ ] User isolation enforced
- [ ] RLS policies active
- [ ] JWT tokens validated
- [ ] File uploads validated
- [ ] Input sanitization done

### Documentation
- [ ] README updated
- [ ] PIPELINE.md complete
- [ ] QUICKSTART.md verified
- [ ] API documentation generated
- [ ] Example requests provided
- [ ] Troubleshooting guide included

## 🚀 Deployment Steps

### Stage 1: Pre-Production Testing (1-2 days)

```bash
# 1. Full environment setup
python -m venv venv
source venv/bin/activate
pip install -r requirements-complete.txt

# 2. Run migrations
# Execute sql/migrations/02_helix_reports.sql in Supabase

# 3. Start services
# Terminal 1: ollama serve
# Terminal 2: uvicorn app.main:app --reload

# 4. Run test suite (if added)
pytest tests/ -v

# 5. Manual API testing
curl http://localhost:8000/health
```

### Stage 2: Staging Deployment (1-2 days)

```bash
# 1. Staging environment
export ENVIRONMENT=staging
export SUPABASE_URL=https://staging-project.supabase.co

# 2. Deploy backend
# Option A: Docker
docker build -t helix-backend .
docker run -p 8000:8000 --env-file .env helix-backend

# Option B: Traditional server
gunicorn -w 4 -b 0.0.0.0:8000 app.main:app

# 3. Run smoke tests
# Upload test file
# Generate report
# Test chat
# Verify data persists

# 4. Load testing
# Use locust or similar
```

### Stage 3: Production Deployment (1 day)

```bash
# 1. Production environment
export ENVIRONMENT=production
export DEBUG=false

# 2. Production database
# Create production Supabase project
# Run migrations
# Enable all security policies

# 3. Production LLM
# Deploy Ollama on dedicated GPU
# Set OLLAMA_URL to production endpoint
# Pull required models

# 4. Deploy backend
# Use load balancer
# Multiple instances recommended
# Monitor resource usage

# 5. Enable monitoring
# Configure Sentry
# Setup Application Insights
# Create CloudWatch logs

# 6. Security hardening
# Enable HTTPS
# Configure SSL certificates
# Set CORS correctly
# Rate limiting enabled
```

## 📋 Post-Deployment Verification

### Functionality Tests
- [ ] User can upload document
- [ ] OCR extracts values
- [ ] Parser normalizes data
- [ ] LLM generates report
- [ ] Report stored in database
- [ ] Can retrieve report
- [ ] Can chat about report
- [ ] Chat history persists
- [ ] Can export report

### Security Tests
- [ ] Unauthorized requests rejected
- [ ] JWT validation works
- [ ] User isolation enforced
- [ ] No diagnosis output
- [ ] No sensitive data in logs
- [ ] SQL injection prevented
- [ ] File upload validated
- [ ] Rate limiting works

### Performance Tests
- [ ] Upload <30 seconds
- [ ] Report generation <60 seconds
- [ ] Chat response <10 seconds
- [ ] List reports <5 seconds
- [ ] No memory leaks
- [ ] CPU usage reasonable
- [ ] Database queries optimized

### Data Integrity Tests
- [ ] Data persists after restart
- [ ] No corruption on errors
- [ ] Transactions work correctly
- [ ] Backups working
- [ ] Disaster recovery tested
- [ ] User data properly isolated

## 🔍 Monitoring Setup

### Logging
- [ ] Sentry configured
- [ ] Application Insights enabled
- [ ] CloudWatch logging active
- [ ] Log rotation configured
- [ ] Error alerts setup

### Metrics
- [ ] Request count tracking
- [ ] Error rate monitoring
- [ ] Response time tracking
- [ ] Database performance
- [ ] GPU/CPU usage (Ollama)
- [ ] Storage usage

### Alerts
- [ ] Error spike alert
- [ ] Service down alert
- [ ] High latency alert
- [ ] Database connection alert
- [ ] Ollama unavailable alert
- [ ] Low disk space alert

## 🛡️ Security Hardening

### Before Production
- [ ] All environment variables encrypted
- [ ] No secrets in version control
- [ ] JWT secret rotated
- [ ] Database password strong
- [ ] API rate limiting enabled
- [ ] CORS properly configured
- [ ] HTTPS enforced
- [ ] HSTS headers enabled
- [ ] Security headers added

### HIPAA Compliance (if needed)
- [ ] Encryption at rest enabled
- [ ] Encryption in transit (TLS)
- [ ] Access logs maintained
- [ ] Audit trail complete
- [ ] Data retention policies set
- [ ] Deletion procedures implemented
- [ ] Business Associate Agreement signed

## 📊 Capacity Planning

### Database
- [ ] Supabase plan sufficient
- [ ] Storage quota adequate
- [ ] Read/write limits acceptable
- [ ] Scaling plan in place

### LLM (Ollama)
- [ ] GPU with sufficient VRAM
- [ ] CPU cores adequate
- [ ] Network bandwidth sufficient
- [ ] Model loading time acceptable
- [ ] Concurrent request handling

### Storage
- [ ] Supabase bucket sized correctly
- [ ] File retention policies set
- [ ] Cleanup scheduled
- [ ] Cost estimates reviewed

## 📈 Performance Baselines

Document baseline performance metrics:

### Response Times (Target)
- Health check: <100ms
- Upload: <30s
- Generate report: <60s
- Chat response: <10s
- List reports: <5s

### Resource Usage
- Backend memory: <500MB
- Ollama memory: <4GB
- Database connections: <20
- Storage: < 100GB

### Throughput
- Concurrent users: 100+
- Requests per second: 50+
- Upload queue: 10+

## 🔄 Rollback Plan

### If Issues Detected

1. **Immediate**
   - Roll back to previous version
   - Revert database migrations (if applicable)
   - Clear FAISS indices if corrupted
   - Notify users

2. **Investigation**
   - Check logs in Sentry
   - Review application metrics
   - Analyze error patterns
   - Identify root cause

3. **Fix & Redeploy**
   - Create bug fix
   - Test in staging
   - Deploy to production
   - Monitor for issues

## 📞 Support Contacts

- [ ] Backend team lead contact
- [ ] On-call rotation setup
- [ ] Escalation procedures defined
- [ ] Documentation updated
- [ ] Runbooks created

## ✨ Post-Launch

### Week 1
- [ ] Monitor error rates
- [ ] Check performance metrics
- [ ] User feedback collection
- [ ] Early issue resolution

### Month 1
- [ ] Performance optimization
- [ ] Cost review
- [ ] Scaling assessment
- [ ] Feature feedback analysis

### Ongoing
- [ ] Regular backups verified
- [ ] Security patches applied
- [ ] Dependency updates
- [ ] Documentation maintenance
- [ ] Team training on procedures

## 🎯 Sign-Off

**Deployment Checklist Completed By:**
- Name: ________________
- Date: ________________
- Signature: ________________

**Approved For Production By:**
- Name: ________________
- Date: ________________
- Signature: ________________

---

**HELIX Backend v1.0 Ready for Production** ✅
