"""
FastAPI dependency injection for authentication
Provides get_current_user() and other auth utilities

Supports DEMO mode when DEMO_MODE=true is set in environment.
In demo mode, all requests are authenticated as a demo user.
"""

import logging
import os
from typing import Dict, Optional
from fastapi import Depends, Request, HTTPException

logger = logging.getLogger(__name__)

DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"

DEMO_USER_PAYLOAD = {
    "sub": "demo-user-001",
    "email": "demo@helix.local",
    "user_metadata": {"role": "user"},
    "email_verified": True,
}


async def get_current_user(request: Request) -> Dict:
    """
    FastAPI dependency: Returns verified user from JWT token.
    In DEMO mode, returns a static demo user payload.
    """
    if DEMO_MODE:
        logger.debug("Demo mode: returning demo user")
        return DEMO_USER_PAYLOAD

    try:
        from app.middleware.jwt_verify import verify_request_token
        payload = verify_request_token(request)
        logger.debug(f"User authenticated: {payload.get('sub')}")
        return payload
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_current_user: {e}")
        raise HTTPException(status_code=401, detail="Authentication required")


async def get_current_user_id(user=Depends(get_current_user)) -> str:
    """Extracts user_id from current user."""
    return user["sub"]


async def get_current_email(user=Depends(get_current_user)) -> str:
    """Extracts email from current user."""
    return user.get("email", "")


async def get_current_user_role(user=Depends(get_current_user)) -> str:
    """Extracts role from current user."""
    user_metadata = user.get("user_metadata", {})
    return user_metadata.get("role", "user")


def require_role(required_role: str):
    """Creates a dependency that requires specific role."""
    async def check_role(role: str = Depends(get_current_user_role)) -> str:
        if role != required_role:
            raise HTTPException(
                status_code=403,
                detail=f"This endpoint requires '{required_role}' role"
            )
        return role
    return check_role


async def get_optional_user(request: Request) -> Optional[Dict]:
    """Optional user authentication - returns None if not authenticated."""
    if DEMO_MODE:
        return DEMO_USER_PAYLOAD
    try:
        from app.middleware.jwt_verify import verify_request_token
        return verify_request_token(request)
    except Exception:
        return None


class AuthContext:
    """Rich context object for authenticated users."""
    def __init__(self, user: Dict):
        self.user = user
        self.user_id = user.get("sub")
        self.email = user.get("email")
        self.role = user.get("user_metadata", {}).get("role", "user")

    def is_admin(self) -> bool:
        return self.role == "admin"

    def is_verified_email(self) -> bool:
        return self.user.get("email_verified", False)


async def get_auth_context(user: Dict = Depends(get_current_user)) -> AuthContext:
    """FastAPI dependency: Returns AuthContext object."""
    return AuthContext(user)
