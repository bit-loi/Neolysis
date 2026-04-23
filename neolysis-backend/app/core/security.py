from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt
from passlib.context import CryptContext
from app.core.interfaces import IPasswordHasher, ITokenService, IEmailService
from app.config import settings
from loguru import logger

# Context for password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class BcryptPasswordHasher(IPasswordHasher):
    def hash(self, password: str) -> str:
        return pwd_context.hash(password)

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

class JWTTokenService(ITokenService):
    def create_access_token(self, subject: str, expires_delta_mins: Optional[int] = None) -> str:
        if expires_delta_mins:
            expire = datetime.now(timezone.utc) + timedelta(minutes=expires_delta_mins)
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            
        to_encode = {"exp": expire, "sub": str(subject)}
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    def decode_access_token(self, token: str) -> Dict[str, Any]:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload
        except jwt.PyJWTError as e:
            raise ValueError("Could not validate credentials") from e

class DummyEmailService(IEmailService):
    async def send_verification_email(self, email: str, token: str) -> None:
        logger.info(f"DUMMY EMAIL: Send verification to {email}. Token: {token}")

    async def send_password_reset_email(self, email: str, token: str) -> None:
        logger.info(f"DUMMY EMAIL: Send password reset to {email}. Token: {token}")

# Dependency Injection Containers
hasher_service = BcryptPasswordHasher()
token_service = JWTTokenService()
email_service = DummyEmailService()
