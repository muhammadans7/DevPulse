import math 
import uuid 
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel.ext.asyncio.session import AsyncSession
from app.db.session import get_session
from app.dependencies import PaginationParams, get_current_user
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.org import AddMemberRequest, OrgCreate, OrgMemberResponse, OrgResponse
from app.services import org_service

router = APIRouter(prefix="/orgs", tags=["Orgs"])

@router.post("", response_model=OrgResponse, status_code=status.HTTP_201_CREATED)
async def create_org(
    payload: OrgCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> OrgResponse:
    """Create a new organization. The caller becomes its admin."""
    try:
        org = await org_service.create_org(session, payload, current_user.id)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An org with this slug already exists")
    return OrgResponse.model_validate(org)


@router.get("", response_model=PaginatedResponse[OrgResponse])
async def list_orgs(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    pagination: Annotated[PaginationParams, Depends()],
) -> PaginatedResponse[OrgResponse]:
    """List all organizations the current user belongs to."""
    orgs, total = await org_service.list_user_orgs(session, current_user.id, pagination.page, pagination.size)
    return PaginatedResponse(
        items=[OrgResponse.model_validate(o) for o in orgs],
        total=total,
        page=pagination.page,
        size=pagination.size,
        pages=math.ceil(total / pagination.size) if total else 0,
    )


@router.get("/{slug}", response_model=OrgResponse)
async def get_org(
    slug: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> OrgResponse:
    """Get org detail by slug. Caller must be a member."""
    org = await org_service.get_org_by_slug(session, slug)
    if org is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Org not found")
    await org_service.require_membership(session, org.id, current_user.id)
    return OrgResponse.model_validate(org)


@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_org(
    slug: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """Delete an org and all its memberships. Caller must be an admin."""
    org = await org_service.get_org_by_slug(session, slug)
    if org is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Org not found")
    await org_service.require_admin(session, org.id, current_user.id)
    await org_service.delete_org(session, org)


@router.get("/{slug}/members", response_model=PaginatedResponse[OrgMemberResponse])
async def list_members(
    slug: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    pagination: Annotated[PaginationParams, Depends()],
) -> PaginatedResponse[OrgMemberResponse]:
    """List members of an org. Caller must be a member."""
    org = await org_service.get_org_by_slug(session, slug)
    if org is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Org not found")
    await org_service.require_membership(session, org.id, current_user.id)
    members, total = await org_service.list_org_members(session, org.id, pagination.page, pagination.size)
    return PaginatedResponse(
        items=[OrgMemberResponse.model_validate(m) for m in members],
        total=total,
        page=pagination.page,
        size=pagination.size,
        pages=math.ceil(total / pagination.size) if total else 0,
    )


@router.post("/{slug}/members", response_model=OrgMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_member(
    slug: str,
    payload: AddMemberRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> OrgMemberResponse:
    """Add a user to the org. Caller must be an admin."""
    org = await org_service.get_org_by_slug(session, slug)
    if org is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Org not found")
    await org_service.require_admin(session, org.id, current_user.id)
    membership = await org_service.add_member(session, org.id, payload.user_id, payload.role)
    return OrgMemberResponse.model_validate(membership)


@router.delete("/{slug}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    slug: str,
    user_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """Remove a member from the org. Caller must be an admin."""
    org = await org_service.get_org_by_slug(session, slug)
    if org is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Org not found")
    await org_service.require_admin(session, org.id, current_user.id)
    await org_service.remove_member(session, org.id, user_id)
