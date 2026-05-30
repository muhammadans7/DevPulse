import uuid 
from fastapi import HTTPException , status 
from sqlalchemy.exc import IntegrityError
from sqlmodel import func , select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.repo import CommitSnapshot, Repo
from app.schemas.repo import RepoCreate

async def create_repo(
    session : AsyncSession,
    org_id : uuid.UUID,
    payload : RepoCreate
) -> Repo : 
    """Register a new repo under an org. raise 409 if github_repo_id already exists"""
    repo = Repo(
        org_id=org_id,
        github_repo_id=payload.github_repo_id,
        full_name=payload.full_name,
        default_branch=payload.default_branch
    )
    session.add(repo)
    try:
        await session.commit()
        await session.refresh(repo)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A repo with this github ID is already registered"
        )
    return repo


async def get_repo(
    session : AsyncSession,
    repo_id : uuid.UUID,
    org_id : uuid.UUID
) -> Repo | None :
    """Return a repo scoped to the org or None"""
    result = await session.exec(
        select(Repo).where(Repo.id == repo_id, Repo.org_id == org_id)
    )
    return result.first()


async def list_org_repos(
    session : AsyncSession,
    org_id : uuid.UUID,
    page : int ,
    size : int ,
) -> tuple[list[Repo] , int]:
    """Return a paginated response for an org & total count"""
    count_result = await session.exec(
        select(func.count()).select_from(Repo).where(Repo.org_id == org_id)
    )
    total = count_result.one()

    result = await session.exec(
        select(Repo)
        .where(Repo.org_id == org_id)
        .offset((page - 1 ) * size)
        .limit(size)
    )
    return list(result.all()) , total 

async def delete_repo(
    session : AsyncSession,
    repo : Repo
) -> None :
    """Delete repo after clearing commit snapshots to satisfy FK constraints"""
    snapshots_result = await session.exec(
        select(CommitSnapshot).where(CommitSnapshot.repo_id == repo.id)
    )

    for s in snapshots_result.all():
        await session.delete(s)
    await session.delete(repo)
    await session.commit()
