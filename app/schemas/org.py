import uuid
from datetime import datetime
from pydantic import BaseModel, field_validator
from app.models.org import OrgPlan, OrgRole


class OrgCreate(BaseModel):
    """Payload for creating a new organization."""

    name: str
    slug: str

    @field_validator("slug")
    @classmethod
    def slug_format(cls, v: str) -> str:
        if not v.replace("-", "").isalnum():
            raise ValueError("slug may only contain letters, numbers, and hyphens")
        return v.lower()


class OrgResponse(BaseModel):
    """Public representation of an organization."""

    id: uuid.UUID
    name: str
    slug: str
    plan: OrgPlan
    created_at: datetime

    model_config = {"from_attributes": True}


class OrgMemberResponse(BaseModel):
    """Membership record showing a user's role within an org."""

    user_id: uuid.UUID
    org_id: uuid.UUID
    role: OrgRole
    joined_at: datetime

    model_config = {"from_attributes": True}


class AddMemberRequest(BaseModel):
    """Payload for adding a user to an organization."""

    user_id: uuid.UUID
    role: OrgRole = OrgRole.MEMBER
