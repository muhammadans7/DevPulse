import uuid
from datetime import datetime
from pydantic import  BaseModel , EmailStr , field_validator
from app.constants.auth import  PASSWORD_MIN_LENGTH

class UserRegister(BaseModel):
    """Payload for creating a new account."""

    email: EmailStr
    password: str
    full_name: str

    @field_validator("password")
    @classmethod
    def password_length(cls, v: str) -> str:
        if len(v) < PASSWORD_MIN_LENGTH:
            raise ValueError(f"Password must be at least {PASSWORD_MIN_LENGTH} characters")
        return v

    @field_validator("full_name")
    @classmethod
    def full_name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("full_name cannot be blank")
        return v.strip()


class UserLogin(BaseModel):
    """Payload for email/password login."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Public representation of a user — never exposes hashed_password."""

    id: uuid.UUID
    email: str
    full_name: str
    is_active: bool
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}  # tells pydantic also accepts objects - read their attributes
    # with getattr instead of dict["key"] because by default pydantic expects a dict needed when sending response
    # user


class TokenResponse(BaseModel):
    """JWT token returned after successful register or login."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse
