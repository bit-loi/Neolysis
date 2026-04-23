from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import token_service, hasher_service, email_service
from app.db.session import get_db
from app.db.repositories import UserRepository
from app.models.user import User
from app.services.auth_service import AuthService
from app.services.narrative_service import NarrativeService
from pydantic import ValidationError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = token_service.decode_access_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except (ValueError, ValidationError):
        raise credentials_exception

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(int(user_id))
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_verified_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    if not current_user.is_verified:
        raise HTTPException(status_code=403, detail="Unverified email address")
    return current_user

def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    user_repo = UserRepository(db)
    return AuthService(user_repo, hasher_service, token_service, email_service)

def get_narrative_service(db: AsyncSession = Depends(get_db)) -> NarrativeService:
    return NarrativeService(db)
