# 🚀 HELIX Auth Quick Start

Complete authentication setup in 10 minutes.

## Prerequisites

- Supabase account (free): [supabase.com](https://supabase.com)
- Python 3.10+ backend running
- Next.js 16+ frontend
- Git & terminal

## Step 1: Create Supabase Project (2 min)

1. Go to [supabase.com](https://supabase.com)
2. Sign in / Create account
3. Click "New Project"
4. Fill details:
   - Organization: Your choice
   - Project name: `helix-medical`
   - Database password: `(strong password)`
   - Region: Closest to you
5. Click "Create new project"
6. Wait 2-3 minutes for project to initialize

## Step 2: Get Supabase Credentials (1 min)

1. Open project dashboard
2. Click "Settings" → "API"
3. Copy:
   - `Project URL` → `SUPABASE_URL`
   - `Anon public key` → `SUPABASE_ANON_KEY`
   - `JWT Secret` (under Auth section) → `SUPABASE_JWT_SECRET`

## Step 3: Configure Backend (2 min)

```bash
cd helix-backend

# Copy .env template
cp .env.example .env

# Edit .env with credentials
# SUPABASE_URL=https://...supabase.co
# SUPABASE_JWT_SECRET=...
# SUPABASE_ANON_KEY=... (optional, for direct DB access)
```

Install JWT packages:

```bash
pip install -r requirements.txt
```

## Step 4: Setup Database (2 min)

1. Open Supabase dashboard → SQL Editor
2. Create new query
3. Copy entire contents of:
   ```
   helix-backend/sql/migrations/01_auth_and_rls.sql
   ```
4. Paste into SQL editor
5. Click "Run"

✅ Database now has RLS enabled!

## Step 5: Configure Frontend (2 min)

```bash
cd helix

# Copy .env template
cp .env.local.example .env.local

# Edit .env.local
# NEXT_PUBLIC_SUPABASE_URL=https://...
# NEXT_PUBLIC_SUPABASE_ANON_KEY=...
# NEXT_PUBLIC_API_URL=http://localhost:8000
```

Install Supabase client:

```bash
npm install @supabase/supabase-js
npm install
```

## Step 6: Start Backend (1 min)

```bash
cd helix-backend

pip install -r requirements.txt  # If not already done

uvicorn app.main:app --reload
```

Expected output:
```
INFO:     Application startup complete
✓ HELIX Backend Ready!
```

Check health:
```bash
curl http://localhost:8000/health
```

## Step 7: Start Frontend (1 min)

```bash
cd helix

npm run dev
```

Frontend: http://localhost:3000

## Step 8: Test Authentication (1 min)

### Create test user in Supabase

1. Open Supabase dashboard
2. Go to "Authentication" → "Users"
3. Click "Add user"
4. Email: `test@example.com`
5. Password: `Test123!`
6. Click "Save"

### Login to frontend

1. Go to http://localhost:3000
2. Click "Sign In" / "Login"
3. Email: `test@example.com`
4. Password: `Test123!`
5. You should be logged in! ✅

### Test protected API

In browser console:

```javascript
// Import from your app
import { apiGet } from "@/lib/api";

// Call protected endpoint
const profile = await apiGet("/api/auth/profile");
console.log(profile);
// Output: { user_id: "...", email: "test@example.com", ... }
```

---

## 🎉 You're All Set!

### What You Have

✅ User authentication (Supabase)  
✅ JWT tokens (RS256 signed)  
✅ Protected API routes (FastAPI)  
✅ Database access control (RLS)  
✅ Frontend API client (with JWT)  

### Next Steps

1. **Add login form** in Next.js:
   ```typescript
   import { LoginForm } from "@/components/LoginForm";
   export default function LoginPage() {
     return <LoginForm />;
   }
   ```

2. **Protect routes** in backend:
   ```python
   @router.get("/profile")
   async def get_profile(user=Depends(get_current_user)):
     return user
   ```

3. **Add user data** to database:
   ```python
   @router.post("/reports")
   async def upload_report(
     user_id: str = Depends(get_current_user_id),
     report: Report
   ):
     # Insert with user_id (RLS enforces this)
     pass
   ```

### Important Files

| File | Purpose |
|------|---------|
| `helix/lib/auth.ts` | Frontend authentication |
| `helix/lib/api.ts` | API calls with JWT |
| `helix-backend/app/dependencies/auth.py` | Backend auth dependencies |
| `helix-backend/app/middleware/jwt_verify.py` | JWT verification |
| `helix-backend/AUTH_IMPLEMENTATION.md` | Full documentation |

### Security Checklist

- ✅ JWT verified with RS256 signature
- ✅ User ID extracted from token (not client header)
- ✅ All queries scoped to user_id
- ✅ RLS enforced at database level
- ✅ Tokens expire automatically (8 hours)
- ✅ Refresh tokens rotate

---

## Troubleshooting

### "Invalid token" on API call

1. Check `SUPABASE_JWT_SECRET` is correct
2. Verify token is not expired
3. Ensure Authorization header format: `Bearer <token>`

### "Cannot fetch public keys"

1. Check `SUPABASE_URL` is correct
2. Verify internet connection
3. Check Supabase status page

### RLS blocking user's own data

1. Run this in Supabase SQL:
   ```sql
   SELECT tablename, rowsecurity
   FROM pg_tables
   WHERE schemaname = 'public';
   ```
   All should show `rowsecurity = true`

2. Test policy works:
   ```sql
   SELECT * FROM reports
   WHERE user_id = auth.uid();
   ```

### Frontend can't connect to backend

1. Ensure backend running: `uvicorn app.main:app --reload`
2. Check `NEXT_PUBLIC_API_URL=http://localhost:8000`
3. Verify CORS enabled in FastAPI

---

## Production Deployment

### Before Going Live

1. **Change to production URLs**
   - Frontend: Update to production domain
   - Backend: Update to production API endpoint
   - Supabase: Use production project

2. **Enable HTTPS**
   - All JWT requests must be HTTPS
   - Use TLS certificates

3. **Set secure cookies**
   - `Secure` flag (HTTPS only)
   - `SameSite=Strict` (CSRF protection)
   - `HttpOnly` (JS can't access)

4. **Update environment**
   ```env
   ENVIRONMENT=production
   LOG_LEVEL=WARNING
   ```

5. **Enable audit logging**
   - Track all authentication events
   - Store in audit_logs table

---

## Support

- **Supabase Docs**: https://supabase.com/docs
- **FastAPI Auth**: https://fastapi.tiangolo.com/tutorial/security/
- **JWT Standard**: https://tools.ietf.org/html/rfc8725
- **HELIX Auth Docs**: See `AUTH_IMPLEMENTATION.md`

---

**Status**: ✅ Production Ready  
**Version**: 1.0.0  
**Last Updated**: 2024-01-18
