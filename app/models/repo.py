import uuid
from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel
from app.utils.datetime import utc_now


class Repo(SQLModel, table=True):
    """A GitHub repository synced under an organization."""

    __tablename__ = "repos"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    org_id: uuid.UUID = Field(foreign_key="organizations.id", index=True)
    github_repo_id: str = Field(unique=True, index=True, max_length=50)
    full_name: str = Field(max_length=255)
    default_branch: str = Field(default="main", max_length=100)
    last_synced_at: Optional[datetime] = Field(default=None)


class CommitSnapshot(SQLModel, table=True):
    """A single commit captured from GitHub during a sync job."""

    __tablename__ = "commit_snapshots"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    repo_id: uuid.UUID = Field(foreign_key="repos.id", index=True)
    sha: str = Field(unique=True, index=True, max_length=40)
    author_github_login: str = Field(index=True, max_length=100)
    additions: int = Field(default=0)
    deletions: int = Field(default=0)
    committed_at: datetime
