import uuid
from datetime import datetime
from enum import Enum
from sqlmodel import Field, SQLModel, UniqueConstraint
from app.utils.datetime import utc_now


class OrgPlan(str, Enum):
    """Subscription plans available for an organization."""

    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class OrgRole(str, Enum):
    """Roles a user can hold within an organization."""

    ADMIN = "admin"
    MEMBER = "member"


class Organization(SQLModel, table=True):
    """A tenant in DevPulse — maps to a team or company."""

    __tablename__ = "organizations"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=100)
    slug: str = Field(unique=True, index=True, max_length=100)
    plan: OrgPlan = Field(default=OrgPlan.FREE)
    created_at: datetime = Field(default_factory=utc_now)


class OrgMembership(SQLModel, table=True):
    """Join table tracking which users belong to which organization and their role."""

    __tablename__ = "org_memberships"

    __table_args__ = (UniqueConstraint("user_id", "org_id", name="uq_user_org"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    org_id: uuid.UUID = Field(foreign_key="organizations.id", index=True)
    role: OrgRole = Field(default=OrgRole.MEMBER)
    joined_at: datetime = Field(default_factory=utc_now)
