"""
Authentication & Authorization - JWT-based auth with role-based access control.
"""
from __future__ import annotations
from datetime import datetime, timedelta
from typing import Optional
import os
import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials
import jwt

logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours
security = HTTPBearer()


class User:
    """User model for authentication."""
    def __init__(self, user_id: str, email: str, role: str = "user"):
        self.user_id = user_id
        self.email = email
        self.role = role  # "admin", "clinician", "researcher", "user"


def create_access_token(user_id: str, email: str, role: str = "user", expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token.
    
    Args:
        user_id: User identifier
        email: User email
        role: User role for authorization
        expires_delta: Token expiration time
        
    Returns:
        JWT token string
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    expire = datetime.utcnow() + expires_delta
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    
    encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    logger.info(f"Token created for user {user_id}")
    return encoded_jwt


def verify_token(token: str) -> dict:
    """
    Verify and decode JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Expired token received")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except jwt.InvalidTokenError:
        logger.warning("Invalid token received")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


async def get_current_user(credentials: HTTPAuthCredentials = Depends(security)) -> User:
    """
    FastAPI dependency to get current authenticated user.
    
    Args:
        credentials: HTTP Bearer credentials
        
    Returns:
        Current user object
        
    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials
    payload = verify_token(token)
    
    user_id = payload.get("sub")
    email = payload.get("email")
    role = payload.get("role", "user")
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    return User(user_id=user_id, email=email, role=role)


def require_role(required_role: str):
    """
    FastAPI dependency to check user role.
    
    Usage:
        @app.get("/admin")
        async def admin_endpoint(user: User = Depends(require_role("admin"))):
            pass
    """
    async def role_checker(user: User = Depends(get_current_user)) -> User:
        role_hierarchy = {"admin": 3, "clinician": 2, "researcher": 1, "user": 0}
        if role_hierarchy.get(user.role, 0) < role_hierarchy.get(required_role, 0):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {required_role} role"
            )
        return user
    
    return role_checker
