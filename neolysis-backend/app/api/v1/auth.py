from fastapi import APIRouter, Depends, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas.user import UserCreate, UserOut
from app.schemas.token import Token
from app.services.auth_service import AuthService
from app.api.deps import get_auth_service
from app.core.rate_limit import limiter

router = APIRouter()

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(
    request: Request,
    user_in: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Register a new user.
    """
    return await auth_service.register_user(user_in)

@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    return await auth_service.login_user(form_data.username, form_data.password)

@router.get("/verify-email")
@limiter.limit("5/minute")
async def verify_email(
    request: Request,
    token: str,
    email: str,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Verify user's email with the token sent to them.
    """
    return await auth_service.verify_email(email, token)
