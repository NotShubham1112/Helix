"""
Integrating Auth into Existing Routes
How to add authentication to your existing FastAPI endpoints
"""

# ============================================================
# PATTERN 1: Protect Existing Routes
# ============================================================

# BEFORE (unprotected):
@router.get("/api/reports")
def get_reports():
    reports = db.query(Report).all()
    return reports

# AFTER (protected):
from app.dependencies.auth import get_current_user_id

@router.get("/api/reports")
def get_reports(user_id: str = Depends(get_current_user_id)):
    # Now scoped to authenticated user
    reports = db.query(Report).filter(
        Report.user_id == user_id  # CRITICAL
    ).all()
    return reports


# ============================================================
# PATTERN 2: Access User Info
# ============================================================

from app.dependencies.auth import get_current_user, get_auth_context

# Get full user payload
@router.get("/api/profile")
def get_profile(user=Depends(get_current_user)):
    return {
        "user_id": user["sub"],
        "email": user["email"],
        "role": user.get("user_metadata", {}).get("role"),
    }

# Get rich context
@router.get("/api/me")
def get_me(auth=Depends(get_auth_context)):
    return {
        "user_id": auth.user_id,
        "email": auth.email,
        "role": auth.role,
        "is_admin": auth.is_admin(),
    }


# ============================================================
# PATTERN 3: Role-Based Access
# ============================================================

from app.dependencies.auth import require_role, require_any_role

# Admin-only
@router.get("/api/admin/users")
def list_users(_=Depends(require_role("admin"))):
    users = db.query(User).all()
    return users

# Doctor or nurse
@router.post("/api/prescription")
def create_prescription(
    _=Depends(require_any_role("doctor", "nurse")),
    user_id: str = Depends(get_current_user_id)
):
    # Create prescription
    pass


# ============================================================
# PATTERN 4: User-Specific Data Operations
# ============================================================

# File upload (scoped to user)
@router.post("/api/upload-report")
async def upload_report(
    file: UploadFile,
    user_id: str = Depends(get_current_user_id),
    auth=Depends(get_auth_context)
):
    import os
    
    # Store file with user_id prefix for isolation
    filename = f"{user_id}_{file.filename}"
    filepath = os.path.join("uploads", filename)
    
    # Save file
    contents = await file.read()
    with open(filepath, "wb") as f:
        f.write(contents)
    
    # Log action
    logger.info(f"User {auth.email} uploaded {file.filename}")
    
    # Store in database with user_id
    report = Report(
        user_id=user_id,
        filename=file.filename,
        filepath=filepath
    )
    db.add(report)
    db.commit()
    
    return {"status": "success"}


# ============================================================
# PATTERN 5: Cross-User Access Prevention
# ============================================================

from fastapi import HTTPException

# WRONG - User might access another user's data
@router.get("/api/reports/{report_id}")
def get_report(report_id: str):
    report = db.query(Report).filter(Report.id == report_id).first()
    return report  # ❌ No user check!

# RIGHT - Verify user owns the data
@router.get("/api/reports/{report_id}")
def get_report(
    report_id: str,
    user_id: str = Depends(get_current_user_id)
):
    report = db.query(Report).filter(
        Report.id == report_id,
        Report.user_id == user_id  # CRITICAL: scope to user
    ).first()
    
    if not report:
        raise HTTPException(
            status_code=404,
            detail="Report not found"
        )
    
    return report


# ============================================================
# PATTERN 6: Optional Authentication
# ============================================================

from app.dependencies.auth import get_optional_user

# Public endpoint with optional auth
@router.get("/api/articles")
def get_articles(
    user=Depends(get_optional_user),
    skip: int = 0,
    limit: int = 10
):
    query = db.query(Article)
    
    if user:
        # User is authenticated - return personalized
        user_id = user["sub"]
        query = query.filter(Article.user_id == user_id)
    else:
        # User not authenticated - return public
        query = query.filter(Article.is_public == True)
    
    return query.offset(skip).limit(limit).all()


# ============================================================
# PATTERN 7: Audit Logging
# ============================================================

import logging

logger = logging.getLogger(__name__)

@router.post("/api/prescription")
def create_prescription(
    prescription_data: PrescriptionSchema,
    user_id: str = Depends(get_current_user_id),
    auth=Depends(get_auth_context)
):
    # Create prescription
    prescription = Prescription(
        user_id=user_id,
        **prescription_data.dict()
    )
    db.add(prescription)
    db.commit()
    
    # Log for audit trail
    logger.info(
        f"Prescription created",
        extra={
            "user_id": user_id,
            "user_email": auth.email,
            "prescription_id": prescription.id,
            "action": "create_prescription"
        }
    )
    
    return prescription


# ============================================================
# PATTERN 8: Handling Authentication Errors
# ============================================================

from fastapi import HTTPException, status

@router.delete("/api/reports/{report_id}")
def delete_report(
    report_id: str,
    user_id: str = Depends(get_current_user_id)
):
    report = db.query(Report).filter(
        Report.id == report_id,
        Report.user_id == user_id
    ).first()
    
    # Not found or not owned by user
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    # Check if user has permission to delete
    if report.is_locked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Report is locked and cannot be deleted"
        )
    
    db.delete(report)
    db.commit()
    
    return {"message": "Report deleted"}


# ============================================================
# PATTERN 9: Batch Operations with User Scoping
# ============================================================

@router.get("/api/reports-by-date/{date}")
def get_reports_by_date(
    date: str,
    user_id: str = Depends(get_current_user_id)
):
    from datetime import datetime, timedelta
    
    try:
        target_date = datetime.fromisoformat(date).date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD"
        )
    
    # Filter by user AND date
    reports = db.query(Report).filter(
        Report.user_id == user_id,  # CRITICAL
        Report.created_at >= datetime.combine(target_date, datetime.min.time()),
        Report.created_at < datetime.combine(
            target_date + timedelta(days=1),
            datetime.min.time()
        )
    ).all()
    
    return reports


# ============================================================
# PATTERN 10: Update Application Main
# ============================================================

# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import (
    upload,
    chat,
    analyze,
    auth_examples  # Add this
)

app = FastAPI(
    title="HELIX Medical AI",
    description="Secure medical AI backend with authentication",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router)
app.include_router(chat.router)
app.include_router(analyze.router)
app.include_router(auth_examples.router)  # Protected route examples

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/")
def root():
    return {"message": "HELIX Medical AI Backend"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


# ============================================================
# SUMMARY: When to Add get_current_user
# ============================================================

"""
ADD get_current_user_id to ANY route that:

✅ Stores user-specific data
✅ Retrieves user's own records
✅ Modifies user's data
✅ Needs audit logging
✅ Restricts access to one user

DON'T add get_current_user to:
❌ Public health checks
❌ Auth login/signup endpoints
❌ Public documentation endpoints
❌ CORS preflight (OPTIONS)

SECURITY RULE:
Every database query that touches user data MUST filter by user_id
"""
