from fastapi import HTTPException, status
from app.db.repositories import UserRepository
from app.schemas.user import UserCreate
from app.schemas.token import Token
from app.core.security import IPasswordHasher, ITokenService, IEmailService
from app.models.user import User
from loguru import logger

class AuthService:
    def __init__(
        self, 
        user_repo: UserRepository, 
        hasher: IPasswordHasher, 
        token_service: ITokenService, 
        email_service: IEmailService
    ):
        self.user_repo = user_repo
        self.hasher = hasher
        self.token_service = token_service
        self.email_service = email_service

    async def register_user(self, user_in: UserCreate) -> User:
        existing_user = await self.user_repo.get_by_email(user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists."
            )
        
        hashed_pwd = self.hasher.hash(user_in.password)
        user = await self.user_repo.create(user_in.email, hashed_pwd)
        
        try:
            await self.email_service.send_verification_email(user.email, user.verification_token)
        except Exception as e:
            logger.error(f"Failed to send email to {user.email}: {e}")
            
        return user

    async def login_user(self, email: str, password: str) -> Token:
        user = await self.user_repo.get_by_email(email)
        
        if not user or not self.hasher.verify(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        access_token = self.token_service.create_access_token(subject=str(user.id))
        return Token(access_token=access_token, token_type="bearer")

    async def verify_email(self, email: str, token: str) -> dict:
        user = await self.user_repo.get_by_email(email)
        
        if not user or user.verification_token != token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification token or email"
            )
            
        if user.is_verified:
            return {"msg": "Email already verified"}
            
        user.is_verified = True
        user.verification_token = None
        await self.user_repo.update(user)
        
        return {"msg": "Email successfully verified"}
