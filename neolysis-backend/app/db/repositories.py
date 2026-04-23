from abc import ABC, abstractmethod
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
import secrets
from datetime import datetime, timezone

class IUserRepository(ABC):
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        pass

    @abstractmethod
    async def get_by_id(self, user_id: int) -> Optional[User]:
        pass

    @abstractmethod
    async def create(self, email: str, hashed_password: str) -> User:
        pass
        
    @abstractmethod
    async def update(self, user: User) -> User:
        pass

class UserRepository(IUserRepository):
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> Optional[User]:
        return await self.db.get(User, user_id)

    async def create(self, email: str, hashed_password: str) -> User:
        verification_token = secrets.token_urlsafe(32)
        user = User(
            email=email,
            hashed_password=hashed_password,
            verification_token=verification_token
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update(self, user: User) -> User:
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
