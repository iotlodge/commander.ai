"""
Authentication and Authorization Module
Provides JWT-based authentication for Commander.ai
"""

from backend.auth.dependencies import get_current_user, get_current_active_user
from backend.auth.models import User
from backend.auth.schemas import UserCreate, UserLogin, UserResponse, Token
from backend.auth.security import create_access_token, verify_password

__all__ = [
    "get_current_user",
    "get_current_active_user",
    "User",
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "Token",
    "create_access_token",
    "verify_password",
]
