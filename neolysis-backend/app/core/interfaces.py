from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class IPasswordHasher(ABC):
    @abstractmethod
    def hash(self, password: str) -> str:
        pass

    @abstractmethod
    def verify(self, plain_password: str, hashed_password: str) -> bool:
        pass

class ITokenService(ABC):
    @abstractmethod
    def create_access_token(self, subject: str, expires_delta_mins: Optional[int] = None) -> str:
        pass

    @abstractmethod
    def decode_access_token(self, token: str) -> Dict[str, Any]:
        pass

class IEmailService(ABC):
    @abstractmethod
    async def send_verification_email(self, email: str, token: str) -> None:
        pass

    @abstractmethod
    async def send_password_reset_email(self, email: str, token: str) -> None:
        pass
