import uuid
from datetime import timedelta
from urllib.parse import urlencode
import httpx
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings
from app.constants.auth import (
    GITHUB_STATE_EXPIRE_MINUTES,
    JWT_EXPIRY_FIELD,
    JWT_SUBJECT_FIELD,
    PASSWORD_HASH_SCHEME,
)
from app.constants.github import (
    GITHUB_OAUTH_AUTHORIZE_URL,
    GITHUB_OAUTH_TOKEN_URL,
    GITHUB_SCOPES,
)
from app.utils.datetime import utc_now

pwd_context = CryptContext(schemes=[PASSWORD_HASH_SCHEME], deprecated="auto")


def hash_password(password: str) -> str:
    """Return bcrypt hash of a plain-text password."""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if plain matches the bcrypt hash."""
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: uuid.UUID) -> str:
    """Encode a signed JWT containing the user's id as the subject claim."""
    expire = utc_now() + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        JWT_SUBJECT_FIELD: str(user_id),
        JWT_EXPIRY_FIELD: expire,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> uuid.UUID:
    """Decode a JWT and return the user id, or raise ValueError if invalid."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str | None = payload.get(JWT_SUBJECT_FIELD)
        if user_id is None:
            raise ValueError("Token missing subject claim")
        
        return uuid.UUID(user_id)
    
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc # raise here caught in routes


def create_github_state_token(user_id: uuid.UUID) -> str:
    """Create a short-lived signed token encoding user_id — used as OAuth state param."""
    expire = utc_now() + timedelta(minutes=GITHUB_STATE_EXPIRE_MINUTES)
    payload = {JWT_SUBJECT_FIELD: str(user_id), JWT_EXPIRY_FIELD: expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_github_state_token(state: str) -> uuid.UUID:
    """Decode the OAuth state param back to a user_id, or raise ValueError if invalid."""
    try:
        payload = jwt.decode(state, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str | None = payload.get(JWT_SUBJECT_FIELD)
        if user_id is None:
            raise ValueError("State token missing subject")
        return uuid.UUID(user_id)
    except JWTError as exc:
        raise ValueError("Invalid or expired state token") from exc


def build_github_oauth_url(state: str) -> str:
    """Build the GitHub authorization URL the user is redirected to."""
    params = urlencode({
        "client_id": settings.github_client_id,
        "redirect_uri": settings.github_redirect_uri,
        "scope": GITHUB_SCOPES,
        "state": state,
    })
    return f"{GITHUB_OAUTH_AUTHORIZE_URL}?{params}"


async def exchange_github_code(code: str) -> str:
    """Exchange a GitHub authorization code for a user access token."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            GITHUB_OAUTH_TOKEN_URL,
            json={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
                "redirect_uri": settings.github_redirect_uri,
            },
            headers={"Accept": "application/json"},
        )
        response.raise_for_status()
        data = response.json()
        access_token: str | None = data.get("access_token")
        if not access_token:
            raise ValueError("GitHub did not return an access token")
        return access_token
