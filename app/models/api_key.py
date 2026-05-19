import uuid
from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel
from app.utils.datetime import utc_now


class ApiKey(SQLModel, table=True):
    """Stores hashed API keys issued to an organization for programmatic access."""

    __tablename__ = "api_keys"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    org_id: uuid.UUID = Field(foreign_key="organizations.id", index=True)
    key_hash: str = Field(index=True)
    name: str = Field(max_length=100)
    expires_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now)
