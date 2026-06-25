from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from app.models.user import UserRole

# Shared properties
class UserBase(BaseModel):
    email: EmailStr
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    role: UserRole = UserRole.LAWYER
    is_active: bool = True

    @field_validator("first_name", "last_name", mode="before")
    @classmethod
    def sanitize_strings(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip()
        return v

# Properties to receive on user creation
class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)

# Properties to receive on user update
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8, max_length=100)

    @field_validator("first_name", "last_name", mode="before")
    @classmethod
    def sanitize_strings(cls, v: Optional[str]) -> Optional[str]:
        if isinstance(v, str):
            return v.strip()
        return v

# Database properties returned to API (excludes password hashes)
class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Schema for Login request
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Schema for Token Response (refresh_token delivered via HttpOnly cookie,
# never in the body — kept out of localStorage / JS access).
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: UserRole
    user_email: EmailStr
    user_name: str

# Schema for Password Reset Request
class PasswordResetRequest(BaseModel):
    email: EmailStr

# Schema for Password Reset Confirmation
class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)
