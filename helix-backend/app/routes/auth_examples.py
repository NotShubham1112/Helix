"""
Protected routes example - demonstrates auth patterns
Real routes should follow these patterns
"""

from fastapi import APIRouter, Depends, HTTPException
from app.dependencies.auth import (
    get_current_user,
    get_current_user_id,
    get_auth_context,
    require_role,
    AuthContext,
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/profile")
async def get_profile(user=Depends(get_current_user)):
    """
    Get authenticated user's profile
    
    SECURITY:
    - Requires valid JWT token
    - Returns only user's own data
    - User ID extracted from verified token, not client header
    """
    return {
        "user_id": user["sub"],
        "email": user["email"],
        "email_verified": user.get("email_verified"),
        "role": user.get("user_metadata", {}).get("role", "user"),
    }


@router.get("/me")
async def get_current_user_info(auth: AuthContext = Depends(get_auth_context)):
    """
    Rich user information using AuthContext
    """
    return {
        "user_id": auth.user_id,
        "email": auth.email,
        "role": auth.role,
        "is_admin": auth.is_admin(),
        "is_verified": auth.is_verified_email(),
    }


@router.get("/reports")
async def get_user_reports(user_id: str = Depends(get_current_user_id)):
    """
    Get reports for authenticated user
    
    SECURITY:
    - user_id extracted from verified JWT
    - Query scoped to user_id
    - RLS in database enforces per-user access
    
    In real implementation:
        reports = db.query(Report).filter(Report.user_id == user_id).all()
        return reports
    """
    return {
        "user_id": user_id,
        "reports": [
            # Placeholder: Real reports from database
            {
                "id": "report-1",
                "title": "Lab Results",
                "date": "2024-01-15",
                "user_id": user_id,  # Guaranteed to be user's own
            }
        ],
    }


@router.post("/upload-report")
async def upload_report(
    user_id: str = Depends(get_current_user_id),
    auth: AuthContext = Depends(get_auth_context),
):
    """
    Upload medical report
    
    SECURITY:
    - user_id guaranteed from token
    - Will be inserted with user_id
    - RLS prevents other users from accessing
    """
    logger.info(f"User {auth.email} uploading report")
    return {
        "status": "success",
        "message": "Report uploaded",
        "user_id": user_id,
    }


# ROLE-BASED ACCESS EXAMPLES

@router.get("/admin/users")
async def list_all_users(
    _=Depends(require_role("admin")),  # Requires admin role
    user=Depends(get_current_user),
):
    """
    List all users - admin only
    
    SECURITY:
    - Requires admin role in JWT
    - Role extracted from user_metadata
    - Non-admins get 403 Forbidden
    """
    logger.info(f"Admin {user['email']} listing all users")
    return {
        "message": "Admin access granted",
        "users": [
            # Placeholder
        ],
    }


@router.get("/doctor/patients")
async def list_doctor_patients(
    _=Depends(require_role("doctor")),  # Requires doctor role
    user=Depends(get_current_user),
):
    """
    List patients - doctor only
    """
    return {
        "doctor": user["email"],
        "patients": [
            # Doctor's patients from database
        ],
    }


@router.post("/prescription")
async def create_prescription(
    _=Depends(require_role("doctor")),  # Doctor or higher
    user_id: str = Depends(get_current_user_id),
):
    """
    Create prescription - requires doctor role
    """
    return {"status": "success", "prescription_id": "rx-123"}


# CONTEXT EXAMPLES

@router.get("/analysis/{report_id}")
async def analyze_report(
    report_id: str,
    auth: AuthContext = Depends(get_auth_context),
):
    """
    Analyze medical report with rich context
    
    SECURITY:
    - user_id from verified token
    - Query: SELECT * FROM reports WHERE id = ? AND user_id = ?
    - RLS prevents access to other users' reports
    """
    logger.info(f"User {auth.email} analyzing report {report_id}")
    
    # In real implementation:
    # report = db.query(Report).filter(
    #     Report.id == report_id,
    #     Report.user_id == auth.user_id  # CRITICAL: scope to user
    # ).first()
    # 
    # if not report:
    #     raise HTTPException(404, "Report not found")
    
    return {
        "report_id": report_id,
        "user_id": auth.user_id,
        "analysis": "Medical analysis results here",
    }


# OPTIONAL AUTH EXAMPLES

@router.get("/public-articles")
async def get_articles(
    skip: int = 0,
    limit: int = 10,
):
    """
    Public endpoint - no auth required
    """
    return {
        "articles": [
            # Public articles
        ],
    }


@router.get("/recommended-articles")
async def get_recommended_articles(
    auth: AuthContext = Depends(get_auth_context),
):
    """
    User-specific recommendations - requires auth
    """
    return {
        "user_id": auth.user_id,
        "recommendations": [
            # Articles recommended for this user's role
        ],
    }
