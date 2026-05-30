from enum import member
import uuid 
from app.schemas.org import OrgCreate
from fastapi import HTTPException, status 
from sqlalchemy.exc import IntegrityError
from sqlmodel import func , select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.org import OrgMembership, OrgRole, Organization
from app.models.repo import CommitSnapshot, Repo

async def create_org(
    session: AsyncSession,
    payload: OrgCreate,
    created_id: uuid.UUID,
) -> Organization:
    """Create org and enroll the creator as admin in one transaction"""
    org = Organization(name=payload.name, slug=payload.slug)
    session.add(org)
    try:
        await session.flush()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An org with this slug already exists")

    membership = OrgMembership(user_id=created_id, org_id=org.id, role=OrgRole.ADMIN)
    session.add(membership)
    await session.commit()
    await session.refresh(org)
    return org


async def get_org_by_slug(session: AsyncSession, slug : str) -> Organization | None :
    """Return org matching slug or None"""
    result = await session.exec(select(Organization).where(Organization.slug == slug))
    return result.first()


async def require_membership(
    session : AsyncSession,
    org_id : uuid.UUID,
    user_id : uuid.UUID,
) -> OrgMembership:
    """Return membership record or raise 403"""

    result = await session.exec(
        select(OrgMembership).where(
            OrgMembership.org_id == org_id,
            OrgMembership.user_id == user_id,
        )
    )

    membership = result.first()
    if membership is None :
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this org")
    return membership


async def require_admin(
    session : AsyncSession,
    org_id : uuid.UUID,
    user_id : uuid.UUID,
) -> OrgMembership:
    """Return membership if admin , raise 403 otherwise"""
    membership = await require_membership(session, org_id, user_id)
    if membership.role != OrgRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return membership


async def list_user_orgs(
    session: AsyncSession,
    user_id: uuid.UUID,
    page: int,
    size: int,
) -> tuple[list[Organization], int]:
    """Return paginated orgs for a user and the total count."""
    count_result = await session.exec(
        select(func.count()).select_from(OrgMembership).where(OrgMembership.user_id == user_id)
    )
    total = count_result.one()

    result = await session.exec(
        select(Organization)
        .join(OrgMembership, Organization.id == OrgMembership.org_id)
        .where(OrgMembership.user_id == user_id)
        .offset((page - 1) * size)
        .limit(size)
    )
    return list(result.all()), total


async def list_org_members(
    session: AsyncSession,
    org_id: uuid.UUID,
    page: int,
    size: int,
) -> tuple[list[OrgMembership], int]:
    """Return paginated memberships for an org and the total count."""
    count_result = await session.exec(
        select(func.count()).select_from(OrgMembership).where(OrgMembership.org_id == org_id)
    )
    total = count_result.one()

    result = await session.exec(
        select(OrgMembership)
        .where(OrgMembership.org_id == org_id)
        .offset((page - 1) * size)
        .limit(size)
    )
    return list(result.all()), total


async def add_member(
    session: AsyncSession,
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    role: OrgRole,
) -> OrgMembership:
    """Add user to org, raise 409 if already a member."""
    membership = OrgMembership(user_id=user_id, org_id=org_id, role=role)
    session.add(membership)
    try:
        await session.commit()
        await session.refresh(membership)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is already a member of this org")
    return membership


async def remove_member(
    session: AsyncSession,
    org_id: uuid.UUID,
    target_user_id: uuid.UUID,
) -> None:
    """Remove a user from an org, raise 404 if not a member."""
    result = await session.exec(
        select(OrgMembership).where(
            OrgMembership.org_id == org_id,
            OrgMembership.user_id == target_user_id,
        )
    )
    membership = result.first()
    if membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found")
    await session.delete(membership)
    await session.commit()


async def delete_org(session: AsyncSession, org: Organization) -> None:
    """Delete org after clearing child rows in FK order: snapshots → repos → memberships → org."""
    repos_result = await session.exec(select(Repo).where(Repo.org_id == org.id))
    for repo in repos_result.all():
        snapshots_result = await session.exec(
            select(CommitSnapshot).where(CommitSnapshot.repo_id == repo.id)
        )
        for s in snapshots_result.all():
            await session.delete(s)
        await session.delete(repo)

    members_result = await session.exec(select(OrgMembership).where(OrgMembership.org_id == org.id))
    for m in members_result.all():
        await session.delete(m)

    await session.delete(org)
    await session.commit()
