import secrets

from fastapi import APIRouter, Depends, HTTPException, status

from app.config import settings
from app.schemas.auth import AuthUser, LoginRequest, LogoutResponse, TokenRequest, TokenResponse
from app.security import get_current_user


router = APIRouter(prefix="/api/auth", tags=["01 Authentication"])


def validate_login(username: str, password: str) -> TokenResponse:
    if not settings.api_auth_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API_AUTH_TOKEN is not configured.",
        )

    if not settings.api_auth_username or not settings.api_auth_password:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API_AUTH_USERNAME and API_AUTH_PASSWORD are required for token login.",
        )

    valid_username = secrets.compare_digest(username, settings.api_auth_username)
    valid_password = secrets.compare_digest(password, settings.api_auth_password)
    if not valid_username or not valid_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    return TokenResponse(access_token=settings.api_auth_token)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and get bearer token",
    description="Login with API_AUTH_USERNAME and API_AUTH_PASSWORD. Copy access_token into Swagger Authorize.",
)
def login(payload: LoginRequest):
    return validate_login(payload.username, payload.password)


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="Get Swagger bearer token",
    description="Alias for /api/auth/login.",
)
def issue_token(payload: TokenRequest):
    return validate_login(payload.username, payload.password)


@router.get(
    "/me",
    response_model=AuthUser,
    summary="Get current authenticated user",
)
def me(user: dict = Depends(get_current_user)):
    return AuthUser(**user)


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="Logout current session",
    description="Bearer tokens are stateless. Remove the token from the client after calling this endpoint.",
)
def logout(user: dict = Depends(get_current_user)):
    return LogoutResponse(message=f"{user['username']} logged out. Remove the bearer token from the client.")
