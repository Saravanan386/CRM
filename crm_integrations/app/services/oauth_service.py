import json
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx

from app.config import settings
from app.utils.encryption import EncryptionService


class OAuthService:
    def __init__(self):
        self.state_crypto = EncryptionService(settings.encryption_key)

    def build_authorization_url(
        self,
        provider: str,
        workspace_name: str,
        login_email: str,
        sync_scope: str = "contacts",
        allow_collab: bool = True,
        auto_sync: bool = True,
    ) -> str | None:
        redirect_uri = f"{settings.api_base_url}/api/crm/auth/{provider}/callback"
        oauth_config = self._oauth_config(provider)
        if not oauth_config:
            return None

        state = self.create_state(
            provider=provider,
            workspace_name=workspace_name,
            login_email=login_email,
            sync_scope=sync_scope,
            allow_collab=allow_collab,
            auto_sync=auto_sync,
        )
        query = urlencode(
            {
                "client_id": oauth_config["client_id"],
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": oauth_config["scope"],
                "state": state,
                "access_type": "offline",
                "prompt": "consent",
            }
        )
        return f"{oauth_config['authorize_url']}?{query}"

    def create_state(
        self,
        provider: str,
        workspace_name: str,
        login_email: str,
        sync_scope: str,
        allow_collab: bool,
        auto_sync: bool,
    ) -> str:
        payload = {
            "provider": provider,
            "workspace_name": workspace_name,
            "login_email": login_email,
            "sync_scope": sync_scope,
            "allow_collab": allow_collab,
            "auto_sync": auto_sync,
            "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat(),
        }
        return self.state_crypto.encrypt(json.dumps(payload))

    def read_state(self, state: str) -> dict[str, str | bool]:
        payload = json.loads(self.state_crypto.decrypt(state))
        expires_at = datetime.fromisoformat(str(payload["expires_at"]))
        if expires_at < datetime.now(timezone.utc):
            raise ValueError("OAuth state expired")
        return payload

    async def exchange_code_for_token(self, provider: str, code: str) -> dict[str, str | int | None]:
        oauth_config = self._oauth_config(provider)
        if not oauth_config:
            raise ValueError("OAuth provider not configured")

        if oauth_config["client_secret"]:
            redirect_uri = f"{settings.api_base_url}/api/crm/auth/{provider}/callback"
            payload = {
                "grant_type": "authorization_code",
                "client_id": oauth_config["client_id"],
                "client_secret": oauth_config["client_secret"],
                "redirect_uri": redirect_uri,
                "code": code,
            }
            async with httpx.AsyncClient(timeout=30) as client:
                try:
                    response = await client.post(
                        oauth_config["token_url"],
                        data=payload,
                        headers={"Accept": "application/json"},
                    )
                    response.raise_for_status()
                    return response.json()
                except httpx.HTTPError as exc:
                    raise ValueError(f"OAuth token exchange failed for {provider}") from exc

        raise ValueError("OAuth client secret not configured")

    def _oauth_config(self, provider: str) -> dict[str, str] | None:
        configs = {
            "salesforce": {
                "client_id": settings.salesforce_client_id,
                "client_secret": settings.salesforce_client_secret,
                "authorize_url": "https://login.salesforce.com/services/oauth2/authorize",
                "token_url": "https://login.salesforce.com/services/oauth2/token",
                "scope": "api refresh_token",
            },
            "hubspot": {
                "client_id": settings.hubspot_client_id,
                "client_secret": settings.hubspot_client_secret,
                "authorize_url": "https://app.hubspot.com/oauth/authorize",
                "token_url": "https://api.hubapi.com/oauth/v1/token",
                "scope": "crm.objects.contacts.read crm.objects.contacts.write",
            },
            "zoho": {
                "client_id": settings.zoho_client_id,
                "client_secret": settings.zoho_client_secret,
                "authorize_url": "https://accounts.zoho.com/oauth/v2/auth",
                "token_url": "https://accounts.zoho.com/oauth/v2/token",
                "scope": "ZohoCRM.modules.ALL",
            },
            "microsoft_d365": {
                "client_id": settings.microsoft_client_id,
                "client_secret": settings.microsoft_client_secret,
                "authorize_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
                "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
                "scope": "https://graph.microsoft.com/.default",
            },
            "keap": {
                "client_id": settings.keap_client_id,
                "client_secret": settings.keap_client_secret,
                "authorize_url": "https://accounts.infusionsoft.com/app/oauth/authorize",
                "token_url": "https://api.infusionsoft.com/token",
                "scope": "full",
            },
        }
        config = configs.get(provider)
        if not config or not config["client_id"]:
            return None
        return config
