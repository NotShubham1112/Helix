"""
JWT Verification Middleware
Validates Supabase JWT tokens and extracts user identity
"""

import logging
from typing import Dict, Optional
from fastapi import Request, HTTPException
from jose import jwt, JWTError
import requests
from functools import lru_cache
import os
from datetime import datetime

logger = logging.getLogger(__name__)

# Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://your-project.supabase.co")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")
ALGORITHM = "RS256"
AUDIENCE = "authenticated"

class JWTVerificationError(Exception):
    """Custom exception for JWT verification failures"""
    pass


class JWKSCache:
    """Cache Supabase public keys to avoid repeated HTTP requests"""
    
    def __init__(self, url: str, cache_ttl: int = 3600):
        self.url = url
        self.cache_ttl = cache_ttl
        self._cache: Optional[Dict] = None
        self._cache_time: Optional[datetime] = None
    
    def get(self) -> Dict:
        """Get JWKS, using cache if valid"""
        now = datetime.utcnow()
        
        if self._cache and self._cache_time:
            age = (now - self._cache_time).total_seconds()
            if age < self.cache_ttl:
                logger.debug(f"Using cached JWKS (age: {age}s)")
                return self._cache
        
        logger.info("Fetching fresh JWKS from Supabase")
        try:
            response = requests.get(self.url, timeout=10)
            response.raise_for_status()
            self._cache = response.json()
            self._cache_time = now
            return self._cache
        except Exception as e:
            logger.error(f"Failed to fetch JWKS: {e}")
            if self._cache:
                logger.warning("Using stale JWKS cache due to fetch failure")
                return self._cache
            raise JWTVerificationError("Failed to fetch Supabase keys")


# Global JWKS cache
jwks_cache = JWKSCache(f"{SUPABASE_URL}/auth/v1/keys")


def get_public_key_for_token(token: str) -> str:
    """
    Extract kid from token header and return corresponding public key
    
    Args:
        token: JWT token
        
    Returns:
        Public key string
        
    Raises:
        JWTVerificationError: If key not found or token header invalid
    """
    try:
        # Get unverified header to extract 'kid' (key ID)
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        
        if not kid:
            raise JWTVerificationError("Token header missing 'kid'")
        
        # Get JWKS (cached or fresh)
        jwks = jwks_cache.get()
        
        # Find matching key
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                # Convert JWK to PEM format
                from jose.backends.rsa_backend import RSAKey
                return RSAKey(key).to_pem()
        
        raise JWTVerificationError(f"Key with kid '{kid}' not found in JWKS")
        
    except JWTError as e:
        raise JWTVerificationError(f"Failed to parse token header: {e}")


def verify_jwt_token(token: str) -> Dict:
    """
    Verify JWT token signature and return payload
    
    SECURITY CRITICAL:
    - Verifies RS256 signature using Supabase public key
    - Validates audience claim
    - Checks expiration
    - Raises exception if ANY check fails
    
    Args:
        token: JWT access token from Supabase
        
    Returns:
        Verified payload with claims
        
    Raises:
        JWTVerificationError: If token invalid, expired, or signature fails
    """
    try:
        # Get appropriate public key for this token
        public_key = get_public_key_for_token(token)
        
        # Verify signature and validate claims
        payload = jwt.decode(
            token,
            public_key,
            algorithms=[ALGORITHM],
            audience=AUDIENCE,
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_aud": True,
            }
        )
        
        # Additional validation
        if "sub" not in payload:
            raise JWTVerificationError("Token missing 'sub' (user_id) claim")
        
        logger.debug(f"✓ Token verified for user: {payload.get('sub')}")
        return payload
        
    except jwt.ExpiredSignatureError:
        raise JWTVerificationError("Token has expired")
    except jwt.JWTClaimsError as e:
        raise JWTVerificationError(f"Invalid token claims: {e}")
    except jwt.JWTError as e:
        raise JWTVerificationError(f"Invalid token: {e}")
    except Exception as e:
        logger.error(f"Unexpected error verifying token: {e}")
        raise JWTVerificationError(f"Token verification failed: {e}")


def extract_token_from_header(auth_header: Optional[str]) -> str:
    """
    Extract Bearer token from Authorization header
    
    Args:
        auth_header: Authorization header value
        
    Returns:
        Token string
        
    Raises:
        JWTVerificationError: If header missing or malformed
    """
    if not auth_header:
        raise JWTVerificationError("Missing Authorization header")
    
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise JWTVerificationError(
            "Invalid Authorization header. Expected: 'Bearer <token>'"
        )
    
    return parts[1]


def verify_request_token(request: Request) -> Dict:
    """
    Complete token verification flow for incoming request
    
    SECURITY CRITICAL: This is the main entry point for auth verification
    
    Flow:
    1. Extract token from Authorization header
    2. Verify JWT signature
    3. Validate claims
    4. Return verified payload
    
    Args:
        request: FastAPI request object
        
    Returns:
        Verified token payload
        
    Raises:
        HTTPException: 401 if missing token, 403 if invalid/expired
    """
    try:
        # Extract token
        auth_header = request.headers.get("Authorization")
        token = extract_token_from_header(auth_header)
        
        # Verify token
        payload = verify_jwt_token(token)
        return payload
        
    except JWTVerificationError as e:
        logger.warning(f"Token verification failed: {e}")
        if "expired" in str(e).lower():
            raise HTTPException(status_code=403, detail=str(e))
        raise HTTPException(status_code=403, detail="Invalid token")
    except Exception as e:
        logger.error(f"Unexpected auth error: {e}")
        raise HTTPException(status_code=401, detail="Authentication required")
