"""
FastAPI dependency injection for authentication
Provides get_current_user() and other auth utilities
"""

import logging
from typing import Dict, Optional
from fastapi import Depends, Request, HTTPException

from app.middleware.jwt_verify import verify_request_token

logger = logging.getLogger(__name__)


async def get_current_user(request: Request) -> Dict:
    """
    FastAPI dependency: Returns verified user from JWT token
    
    Usage:
        @router.get("/profile")
        def get_profile(user=Depends(get_current_user)):
            return {"user_id": user["sub"], "email": user["email"]}
    
    SECURITY: Returns verified payload from JWT. Token must be:
    - Present in Authorization header
    - Valid RS256 signature
    - Not expired
    - Has required claims (sub, email)
    
    Args:
        request: FastAPI request object
        
    Returns:
        Verified JWT payload with claims
        
    Raises:
        HTTPException: 401 if missing token, 403 if invalid/expired
    """
    try:
        payload = verify_request_token(request)
        logger.debug(f"✓ User authenticated: {payload.get('sub')}")
        return payload
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_current_user: {e}")
        raise HTTPException(status_code=401, detail="Authentication required")


async def get_current_user_id(user=Depends(get_current_user)) -> str:
    """
    Extracts user_id from current user
    
    Usage:
        @router.get("/reports")
        def get_reports(user_id: str = Depends(get_current_user_id)):
            return db.query(Report).filter(Report.user_id == user_id)
    
    Args:
        user: Verified user from get_current_user()
        
    Returns:
        User ID (sub claim from JWT)
    """
    return user["sub"]


async def get_current_email(user=Depends(get_current_user)) -> str:
    """
    Extracts email from current user
    
    Args:
        user: Verified user from get_current_user()
        
    Returns:
        User email address
    """
    return user.get("email", "")


async def get_current_user_role(user=Depends(get_current_user)) -> str:
    """
    Extracts role from current user
    
    Usage:
        @router.get("/admin/users")
        def list_users(role: str = Depends(get_current_user_role)):
            if role != "admin":
                raise HTTPException(403, "Insufficient permissions")
            return users
    
    Args:
        user: Verified user from get_current_user()
        
    Returns:
        User role from user_metadata or empty string
    """
    user_metadata = user.get("user_metadata", {})
    return user_metadata.get("role", "user")


def require_role(required_role: str):
    """
    Creates a dependency that requires specific role
    
    Usage:
        @router.get("/admin/users")
        def list_users(user_id = Depends(require_role("admin"))):
            return users
    
    Args:
        required_role: Role required for access
        
    Returns:
        Dependency function
    """
    async def check_role(role: str = Depends(get_current_user_role)) -> str:
        if role != required_role:
            logger.warning(f"Access denied: required role '{required_role}', got '{role}'")
            raise HTTPException(
                status_code=403,
                detail=f"This endpoint requires '{required_role}' role"
            )
        return role
    
    return check_role


def require_any_role(*roles: str):
    """
    Creates a dependency that requires one of multiple roles
    
    Usage:
        @router.get("/reports")
        def get_reports(
            user_id = Depends(require_any_role("doctor", "nurse"))
        ):
            return reports
    
    Args:
        *roles: One or more acceptable roles
        
    Returns:
        Dependency function
    """
    async def check_any_role(role: str = Depends(get_current_user_role)) -> str:
        if role not in roles:
            logger.warning(
                f"Access denied: required role in {roles}, got '{role}'"
            )
            raise HTTPException(
                status_code=403,
                detail=f"This endpoint requires one of these roles: {', '.join(roles)}"
            )
        return role
    
    return check_any_role


class AuthContext:
    """
    Container for authenticated request context
    Provides easy access to user identity and claims
    """
    
    def __init__(self, payload: Dict):
        self.payload = payload
        self.user_id = payload.get("sub")
        self.email = payload.get("email")
        self.role = payload.get("user_metadata", {}).get("role", "user")
        self.is_verified = payload.get("email_verified", False)
    
    def is_admin(self) -> bool:
        """Check if user is admin"""
        return self.role == "admin"
    
    def is_verified_email(self) -> bool:
        """Check if user's email is verified"""
        return self.is_verified
    
    def __repr__(self):
        return f"AuthContext(user_id={self.user_id}, email={self.email}, role={self.role})"


async def get_auth_context(user=Depends(get_current_user)) -> AuthContext:
    """
    Returns rich authentication context
    
    Usage:
        @router.get("/profile")
        def get_profile(auth: AuthContext = Depends(get_auth_context)):
            if not auth.is_verified_email():
                raise HTTPException(400, "Email not verified")
            return {"user_id": auth.user_id, "role": auth.role}
    
    Args:
        user: Verified user from get_current_user()
        
    Returns:
        AuthContext object with convenience methods
    """
    return AuthContext(user)


# Optional: Permit unsigned/guest requests for public endpoints
# Use with caution - most endpoints should require authentication

async def get_optional_user(request: Request) -> Optional[Dict]:
    """
    Optional user authentication - returns None if not authenticated
    
    Usage (for public endpoints with optional auth):
        @router.get("/articles")
        def get_articles(user: Optional[Dict] = Depends(get_optional_user)):
            if user:
                # User-specific content
                articles = db.query(Article).filter(Article.user_id == user["sub"])
            else:
                # Public content
                articles = db.query(Article).filter(Article.is_public == True)
            return articles
    
    Args:
        request: FastAPI request object
        
    Returns:
        Verified user payload if token present and valid, None otherwise
    """
    try:
        return verify_request_token(request)
    except Exception:
        # No token or invalid token - return None for optional auth
        return None
