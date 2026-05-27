import uuid
from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel
from app.utils.datetime import utc_now


class User(SQLModel, table=True):
    """Represents a registered DevPulse user."""

    __tablename__ = "users"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    hashed_password: str
    full_name: str = Field(max_length=255)
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)
    github_access_token: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
