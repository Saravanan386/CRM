import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings


bearer_scheme = HTTPBearer(
    scheme_name="Backend Bearer Token",
    description="Paste your API_AUTH_TOKEN value here.",
    bearerFormat="API_AUTH_TOKEN",
    auto_error=False,
)


def require_api_token(credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)):
    if not settings.api_auth_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API_AUTH_TOKEN is not configured.",
        )

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Open Swagger Authorize and paste API_AUTH_TOKEN.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if credentials.scheme.lower() != "bearer" or not secrets.compare_digest(
        credentials.credentials,
        settings.api_auth_token,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return True


def get_current_user(authenticated: bool = Depends(require_api_token)):
    return {
        "username": settings.api_auth_username or "api-user",
        "authenticated": authenticated,
    }
