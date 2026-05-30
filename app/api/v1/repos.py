import math 
import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status 
from sqlmodel.ext.asyncio.session import AsyncSession
from app.db.session import get_session
from app.dependencies import PaginationParams, get_current_user
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.repo import RepoCreate, RepoResponse
from app.services import org_service , repo_service

router = APIRouter(prefix="/orgs", tags=["Repos"])

@router.post("/{slug}/repos", response_model=RepoResponse, status_code=status.HTTP_201_CREATED)
async def create_repo(
    slug : str ,
    payload : RepoCreate,
    current_user : Annotated[User , Depends(get_current_user)],
    session : Annotated[AsyncSession, Depends(get_session)]
) -> RepoResponse:
    """Register a repo under an org. caller must be admin"""
    org = await org_service.get_org_by_slug(session=session, slug=slug)
    if org is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Org not found")
    
    await org_service.require_admin(session, org.id, current_user.id)
    repo = await repo_service.create_repo(session, org.id, payload)
    
    return RepoResponse.model_validate(repo)

@router.get("/{slug}/repos", response_model=PaginatedResponse[RepoResponse])
async def list_repos(
    slug : str ,
    current_user : Annotated[User, Depends(get_current_user)],
    session : Annotated[AsyncSession, Depends(get_session)],
    pagination : Annotated[PaginationParams, Depends()],
) -> PaginatedResponse[RepoResponse]:
    """List repos for an org caller of api must be member of org"""
    org = await org_service.get_org_by_slug(session, slug)
    if org is None :
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Org not found")
    await org_service.require_membership(session, org.id , current_user.id)
    repos, total = await repo_service.list_org_repos(session, org.id, pagination.page, pagination.size)
    return PaginatedResponse(
        items=[RepoResponse.model_validate(r) for r in repos],
        total=total,
        page=pagination.page,
        size=pagination.size,
        pages=math.ceil(total/pagination.size) if total else 0
    )

@router.get("/{slug}/repos/{repo_id}", response_model=RepoResponse)
async def get_repo(
    slug: str,
    repo_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> RepoResponse:
    """Get a single repo by id. Caller must be a member."""
    org = await org_service.get_org_by_slug(session, slug)
    if org is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Org not found")
    await org_service.require_membership(session, org.id, current_user.id)
    repo = await repo_service.get_repo(session, repo_id, org.id)
    if repo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repo not found")
    return RepoResponse.model_validate(repo)


@router.delete("/{slug}/repos/{repo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_repo(
    slug: str,
    repo_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """Delete a repo and its commit snapshots. Caller must be admin."""
    org = await org_service.get_org_by_slug(session, slug)
    if org is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Org not found")
    await org_service.require_admin(session, org.id, current_user.id)
    repo = await repo_service.get_repo(session, repo_id, org.id)
    if repo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repo not found")
    await repo_service.delete_repo(session, repo)
