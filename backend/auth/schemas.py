"""
Pydantic Schemas for Authentication API
Request and response models for auth endpoints
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema with common fields"""

    email: EmailStr


class UserCreate(UserBase):
    """Schema for user registration"""

    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Password (8-100 characters)",
    )


class UserLogin(UserBase):
    """Schema for user login"""

    password: str


class UserResponse(UserBase):
    """Schema for user data in API responses"""

    id: UUID
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    """Schema for JWT token response"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Schema for JWT token payload"""

    sub: str  # Subject (user_id)
    exp: int  # Expiration timestamp
    type: str  # "access" or "refresh"


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request"""

    refresh_token: str
