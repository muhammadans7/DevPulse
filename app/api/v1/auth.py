from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.db.session import get_session
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import TokenResponse, UserRegister, UserResponse
from app.services.auth_service import (
    build_github_oauth_url,
    create_access_token,
    create_github_state_token,
    decode_github_state_token,
    exchange_github_code,
    hash_password,
    verify_password,
)
from app.utils.datetime import utc_now


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: UserRegister,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TokenResponse:
    """Register a new account and return a JWT."""
    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
    )
    session.add(user)
    try:
        await session.commit()
        await session.refresh(user)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.post("/login", response_model=TokenResponse)
async def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TokenResponse:
    """Authenticate with email and password and return a JWT. Use email in the username field."""
    result = await session.exec(select(User).where(User.email == form.username))
    user = result.first()
    if user is None or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )
    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserResponse:
    """Return the profile of the currently authenticated user."""
    return UserResponse.model_validate(current_user)


@router.get("/github/authorize")
async def github_authorize(
    current_user: Annotated[User, Depends(get_current_user)],
) -> RedirectResponse:
    """Redirect the authenticated user to GitHub's OAuth authorization page."""
    state = create_github_state_token(current_user.id)
    return RedirectResponse(url=build_github_oauth_url(state=state))


@router.get("/github/callback")
async def github_callback(
    code: Annotated[str, Query()],
    state: Annotated[str, Query()],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UserResponse:
    """Handle GitHub's redirect, exchange code for token, and store it on the user."""
    try:
        user_id = decode_github_state_token(state)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OAuth state",
        )
    try:
        github_token = await exchange_github_code(code)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to exchange GitHub authorization code",
        )
    result = await session.exec(select(User).where(User.id == user_id))
    user = result.first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    user.github_access_token = github_token
    user.updated_at = utc_now()
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return UserResponse.model_validate(user)
