from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from urllib.parse import urlencode

from app.config import settings
from app.database import get_db
from app.models.crm_connection import CRMConnection
from app.schemas.crm_connection import CRMConnectionCreate, CRMConnectionRead
from app.routers.crm import save_connection
from app.services.oauth_service import OAuthService
from app.services.token_service import TokenService


router = APIRouter(prefix="/api/crm/auth", tags=["crm-auth"])
oauth_service = OAuthService()
token_service = TokenService()


class OAuthCallbackPayload(BaseModel):
    code: str
    workspace_name: str
    login_email: str
    sync_scope: str = "contacts"
    allow_collab: bool = True
    auto_sync: bool = True


def frontend_redirect(**params):
    return RedirectResponse(f"{settings.frontend_base_url}/crm/connections?{urlencode(params)}")


@router.get("/{provider}/login-url")
def get_login_url(
    provider: str,
    workspace_name: str = Query(..., min_length=1),
    login_email: str = Query(..., min_length=3),
    sync_scope: str = "contacts",
    allow_collab: bool = True,
    auto_sync: bool = True,
):
    url = oauth_service.build_authorization_url(
        provider=provider,
        workspace_name=workspace_name,
        login_email=login_email,
        sync_scope=sync_scope,
        allow_collab=allow_collab,
        auto_sync=auto_sync,
    )
    if not url:
        raise HTTPException(status_code=404, detail="OAuth provider not configured")
    return {"provider": provider, "login_url": url}


@router.get("/{provider}/connect")
def redirect_to_provider_login(
    provider: str,
    workspace_name: str = Query(..., min_length=1),
    login_email: str = Query(..., min_length=3),
    sync_scope: str = "contacts",
    allow_collab: bool = True,
    auto_sync: bool = True,
):
    url = oauth_service.build_authorization_url(
        provider=provider,
        workspace_name=workspace_name,
        login_email=login_email,
        sync_scope=sync_scope,
        allow_collab=allow_collab,
        auto_sync=auto_sync,
    )
    if not url:
        raise HTTPException(status_code=404, detail="OAuth provider not configured")
    return RedirectResponse(url)


@router.post("/{provider}/callback", response_model=CRMConnectionRead)
async def oauth_callback_post(provider: str, payload: OAuthCallbackPayload, db: Session = Depends(get_db)):
    token_response = await oauth_service.exchange_code_for_token(provider, payload.code)
    refresh_token = token_response.get("refresh_token")
    connection_payload = CRMConnectionCreate(
        provider=provider,
        workspace_name=payload.workspace_name,
        login_email=payload.login_email,
        credential=token_response["access_token"],
        sync_scope=payload.sync_scope,
        allow_collab=payload.allow_collab,
        auto_sync=payload.auto_sync,
    )
    encrypted_refresh_token = token_service.encrypt_token(str(refresh_token)) if refresh_token else None
    return save_connection(connection_payload, db, encrypted_refresh_token=encrypted_refresh_token)


@router.get("/{provider}/callback")
async def oauth_callback_get(
    provider: str,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
):
    if error:
        return frontend_redirect(provider=provider, status="error", message=error)
    if not code or not state:
        return frontend_redirect(provider=provider, status="error", message="missing_code")

    try:
        state_payload = oauth_service.read_state(state)
        if state_payload["provider"] != provider:
            raise ValueError("OAuth provider mismatch")
        token_response = await oauth_service.exchange_code_for_token(provider, code)
    except ValueError as exc:
        return frontend_redirect(provider=provider, status="error", message=str(exc))

    now_connection = db.query(CRMConnection).filter(CRMConnection.provider == provider).first()
    access_token = token_service.encrypt_token(str(token_response["access_token"]))
    refresh_token = token_response.get("refresh_token")

    if now_connection:
        now_connection.workspace_name = str(state_payload["workspace_name"])
        now_connection.login_email = str(state_payload["login_email"])
        now_connection.encrypted_access_token = access_token
        now_connection.encrypted_refresh_token = token_service.encrypt_token(str(refresh_token)) if refresh_token else None
        now_connection.sync_scope = str(state_payload["sync_scope"])
        now_connection.allow_collab = bool(state_payload["allow_collab"])
        now_connection.auto_sync = bool(state_payload["auto_sync"])
        now_connection.status = "connected"
        connection = now_connection
    else:
        connection = CRMConnection(
            provider=provider,
            workspace_name=str(state_payload["workspace_name"]),
            login_email=str(state_payload["login_email"]),
            encrypted_access_token=access_token,
            encrypted_refresh_token=token_service.encrypt_token(str(refresh_token)) if refresh_token else None,
            sync_scope=str(state_payload["sync_scope"]),
            allow_collab=bool(state_payload["allow_collab"]),
            auto_sync=bool(state_payload["auto_sync"]),
            status="connected",
        )
        db.add(connection)

    db.commit()
    db.refresh(connection)
    return frontend_redirect(provider=provider, status="connected", connection_id=connection.id)
