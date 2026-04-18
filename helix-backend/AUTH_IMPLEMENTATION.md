# 🔐 HELIX Authentication System Documentation

Complete guide to implementing secure authentication across Next.js frontend, Supabase Auth, and FastAPI backend.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Setup Instructions](#setup-instructions)
3. [Frontend Implementation](#frontend-implementation)
4. [Backend Implementation](#backend-implementation)
5. [Security Best Practices](#security-best-practices)
6. [API Reference](#api-reference)
7. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER AUTHENTICATION FLOW                      │
└─────────────────────────────────────────────────────────────────┘

1. USER LOGS IN
   └─▶ Next.js Form
   └─▶ Supabase Auth
   └─▶ JWT Token Generated

2. FRONTEND STORES TOKEN
   └─▶ httpOnly Cookie (secure)
   └─▶ Memory (fast access)

3. FRONTEND MAKES API REQUEST
   └─▶ Authorization: Bearer <JWT>

4. BACKEND VERIFIES TOKEN
   └─▶ Fetch Supabase public keys
   └─▶ Verify RS256 signature
   └─▶ Extract user_id from payload

5. BACKEND EXECUTES LOGIC
   └─▶ Scope all queries to user_id
   └─▶ Database RLS enforces access control

6. RESPONSE WITH USER DATA
   └─▶ Only user's own data returned
```

### Key Security Properties

| Property | Implementation | Benefit |
|----------|-----------------|---------|
| **Stateless** | JWT tokens, no session table | Scales horizontally |
| **Cryptographic** | RS256 signature verification | Tokens can't be forged |
| **Verified Identity** | Extract user_id from JWT, not client header | Impossible to spoof |
| **Layered Control** | Backend + RLS + Supabase policies | Defense in depth |
| **Token Expiration** | 8-hour access token + refresh token | Limits exposure window |

---

## Setup Instructions

### 1. Supabase Project Creation

1. Go to [supabase.com](https://supabase.com)
2. Create new project
3. Get credentials from Project Settings:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY` (safe to expose)
   - `SUPABASE_SERVICE_ROLE_KEY` (keep secret!)

### 2. Configure Backend (.env)

```bash
cd helix-backend

# Copy and fill .env
cp .env.example .env
```

Edit `.env`:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_JWT_SECRET=your-jwt-secret-from-supabase-keys
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### 3. Configure Frontend (.env.local)

```bash
cd helix

# Copy and fill .env.local
cp .env.local.example .env.local
```

Edit `.env.local`:

```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-from-supabase
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 4. Apply Database Migrations

1. Open Supabase Dashboard
2. Go to SQL Editor
3. Create new query
4. Copy contents of `sql/migrations/01_auth_and_rls.sql`
5. Run the query

Verify RLS is enabled:

```bash
# In Supabase SQL Editor, run:
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;
```

Expected output: All tables should have `rowsecurity = true`

### 5. Install Dependencies

**Backend:**

```bash
cd helix-backend
pip install -r requirements.txt
```

**Frontend:**

```bash
cd helix
npm install @supabase/supabase-js
npm install
```

---

## Frontend Implementation

### 1. Initialize Supabase Client

File: `lib/supabase.ts`

```typescript
import { createClient } from "@supabase/supabase-js";

export const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);
```

### 2. Authentication Functions

File: `lib/auth.ts`

```typescript
import { auth } from "@/lib/auth";

// Sign up
await auth.signUp("user@example.com", "password");

// Sign in
await auth.signIn("user@example.com", "password");

// Get current user
const user = await auth.getCurrentUser();

// Sign out
await auth.signOut();

// Subscribe to auth state
const unsubscribe = onAuthStateChange((user) => {
  setUser(user);
});
```

### 3. API Calls with JWT

File: `lib/api.ts`

All API calls automatically include JWT token:

```typescript
import { apiGet, apiPost, apiDelete } from "@/lib/api";

// GET request (JWT automatically included)
const profile = await apiGet("/api/auth/profile");

// POST request
const analysis = await apiPost("/api/analyze", {
  data: labResults,
});

// DELETE request
await apiDelete("/api/reports/123");

// File upload
await apiUploadFile("/api/upload", file, {
  report_type: "lab",
});
```

### 4. Login Component Example

```tsx
"use client";

import { useState } from "react";
import { auth } from "@/lib/auth";
import { useRouter } from "next/navigation";

export function LoginForm() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      await auth.signIn(email, password);
      router.push("/dashboard");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Login failed"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleLogin}>
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Email"
        required
      />
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Password"
        required
      />
      {error && <div style={{ color: "red" }}>{error}</div>}
      <button type="submit" disabled={loading}>
        {loading ? "Signing in..." : "Sign In"}
      </button>
    </form>
  );
}
```

### 5. Protected Pages (Server-Side)

```tsx
// app/dashboard/page.tsx

import { redirect } from "next/navigation";
import { createServerComponentClient } from "@supabase/auth-helpers-nextjs";
import { cookies } from "next/headers";

export default async function Dashboard() {
  const supabase = createServerComponentClient({ cookies });
  
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login");
  }

  return (
    <div>
      <h1>Welcome, {user.email}</h1>
      {/* Dashboard content */}
    </div>
  );
}
```

---

## Backend Implementation

### 1. JWT Verification Middleware

File: `app/middleware/jwt_verify.py`

Verifies RS256 signature using Supabase public keys:

```python
from app.middleware.jwt_verify import verify_jwt_token

# Verify and get payload
payload = verify_jwt_token(token)
user_id = payload["sub"]  # Guaranteed to be correct
```

### 2. Protected Routes

File: `app/routes/auth_examples.py`

All protected routes require JWT:

```python
from fastapi import APIRouter, Depends
from app.dependencies.auth import get_current_user

router = APIRouter()

@router.get("/profile")
async def get_profile(user=Depends(get_current_user)):
    """
    SECURITY:
    - Requires valid JWT token in Authorization header
    - user_id extracted from verified token
    - Returns only authenticated user's data
    """
    return {
        "user_id": user["sub"],
        "email": user["email"],
    }
```

### 3. User-Scoped Queries

```python
from app.dependencies.auth import get_current_user_id

@router.get("/reports")
async def get_reports(user_id: str = Depends(get_current_user_id)):
    """
    Returns reports only for authenticated user
    
    SECURITY:
    - user_id guaranteed from verified JWT
    - Database RLS enforces this at SQL level
    """
    # Backend filter (defense in depth)
    reports = db.query(Report).filter(
        Report.user_id == user_id  # CRITICAL: Always scope to user
    ).all()
    
    # RLS in database also enforces this
    return reports
```

### 4. Role-Based Access

```python
from app.dependencies.auth import require_role

@router.get("/admin/users")
async def list_users(_=Depends(require_role("admin"))):
    """Requires admin role from JWT"""
    users = db.query(User).all()
    return users

@router.post("/prescription")
async def create_prescription(
    _=Depends(require_role("doctor")),
    user_id: str = Depends(get_current_user_id)
):
    """Requires doctor role"""
    # Create prescription logic
    pass
```

### 5. Update main.py

Add routes to FastAPI app:

```python
# app/main.py

from fastapi import FastAPI
from app.routes import auth_examples

app = FastAPI()

# Include auth routes
app.include_router(auth_examples.router)

# ... other setup
```

---

## Security Best Practices

### ✅ DO:

- **Use HTTPS** in production (JWT transmitted in plain text otherwise)
- **Verify JWT signature** every single request
- **Store JWT in httpOnly cookies** (JavaScript can't access)
- **Scope queries to user_id** from JWT, never from client
- **Implement RLS** at database layer (defense in depth)
- **Enable Row Level Security** on all tables
- **Rotate refresh tokens** automatically
- **Use Supabase Auth** for user management (don't roll your own)
- **Log authentication events** to audit trail
- **Test with invalid tokens** to ensure verification works

### ❌ DON'T:

- **Trust client-provided user_id** - Always extract from verified JWT
- **Skip JWT signature verification** - Always verify cryptographic signature
- **Store JWT in localStorage** - Vulnerable to XSS attacks
- **Expose SERVICE_ROLE_KEY** in frontend (only use ANON_KEY)
- **Disable RLS** - This is your database-level security
- **Make unscoped database queries** - Always filter by user_id
- **Hard-code tokens** in code or environment files
- **Transmit JWT over HTTP** - Use HTTPS only
- **Ignore token expiration** - Always check exp claim
- **Mix authentication schemes** - Use JWT consistently

---

## API Reference

### Frontend

#### `auth.signUp(email, password)`

Register new user with Supabase Auth

```typescript
const { data } = await auth.signUp(
  "user@example.com",
  "secure-password"
);
```

#### `auth.signIn(email, password)`

Authenticate user and get JWT token

```typescript
const { data } = await auth.signIn(
  "user@example.com",
  "password"
);
```

#### `auth.getCurrentUser()`

Get authenticated user object

```typescript
const user = await auth.getCurrentUser();
// Returns: { id, email, user_metadata, ... }
```

#### `apiGet(endpoint)` / `apiPost(endpoint, data)`

Make authenticated API calls

```typescript
// All requests automatically include JWT token
const profile = await apiGet("/api/profile");
const result = await apiPost("/api/analyze", { data });
```

### Backend

#### `get_current_user(request)`

Dependency injection - verifies JWT and returns payload

```python
@router.get("/profile")
async def get_profile(user=Depends(get_current_user)):
    return {"user_id": user["sub"]}
```

#### `get_current_user_id(user)`

Extract user_id from verified JWT

```python
@router.get("/reports")
async def get_reports(user_id: str = Depends(get_current_user_id)):
    reports = db.query(Report).filter(Report.user_id == user_id)
    return reports
```

#### `require_role(role)`

Dependency injection - requires specific role

```python
@router.get("/admin")
async def admin_endpoint(_=Depends(require_role("admin"))):
    return {"message": "Admin access"}
```

---

## Troubleshooting

### Issue: "Invalid token" Error

**Cause:** JWT signature verification failed

**Solutions:**
1. Verify `SUPABASE_URL` and `SUPABASE_JWT_SECRET` in .env
2. Check JWT is not expired: `exp` claim > current time
3. Ensure token format is: `Authorization: Bearer <token>`

### Issue: "Missing Authorization header"

**Cause:** Frontend didn't include JWT in request

**Solutions:**
1. Check token is stored: `auth.getAccessToken()`
2. Verify API call uses `apiGet`/`apiPost` (not raw `fetch`)
3. Check CORS headers allow Authorization

### Issue: 403 Forbidden on User's Own Data

**Cause:** RLS policy not working correctly

**Solutions:**
1. Verify RLS is enabled: Check Supabase SQL output
2. Check RLS policy uses `auth.uid()` correctly
3. Test policy: `SELECT * FROM reports WHERE user_id = auth.uid();`
4. Ensure backend also filters by user_id

### Issue: Token Expires During Request

**Cause:** JWT token expired (valid for ~8 hours)

**Solutions:**
1. Supabase automatically refreshes (check refresh token)
2. Frontend handles 403 response and retries
3. If stuck, require user to sign in again

### Issue: CORS Error

**Cause:** Browser blocking cross-origin request

**Solutions:**
1. Check CORS headers in FastAPI
2. Ensure frontend URL in Supabase auth settings
3. For development: Use `http://localhost:3000`

---

## Production Deployment

### 1. Environment Setup

Update `.env` for production:

```env
ENVIRONMENT=production
SUPABASE_URL=https://prod-project.supabase.co
SUPABASE_JWT_SECRET=prod-secret
LOG_LEVEL=WARNING
```

### 2. HTTPS Requirement

All JWT requests must use HTTPS (or token visible in network tab)

### 3. Token Security

- Use httpOnly cookies (not localStorage)
- Set `SameSite=Strict` on cookies
- Set `Secure` flag on HTTPS-only cookies

### 4. Rate Limiting

Implement rate limiting on `/auth/*` endpoints:

```python
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@app.post("/auth/login")
@limiter.limit("5/minute")
async def login(...):
    pass
```

### 5. Audit Logging

Log all authentication events:

```python
# Log successful login
audit_log_action("user_login", "auth", user_id)

# Log failed attempts
audit_log_action("login_failed", "auth", details={"email": email})
```

---

## Additional Resources

- [Supabase Auth Documentation](https://supabase.com/docs/guides/auth)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Next.js Authentication](https://nextjs.org/docs/authentication)
- [OWASP: Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)

---

**Last Updated:** 2024-01-18  
**HELIX Version:** 1.0.0
