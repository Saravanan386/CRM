from datetime import datetime
from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, EmailStr, Field


CRMProvider = Literal[
    "salesforce",
    "hubspot",
    "zoho",
    "pipedrive",
    "microsoft_d365",
    "freshsales",
    "copper",
    "insightly",
    "keap",
]

SyncScope = Literal["contacts", "leads", "deals", "full"]


class CRMCatalogItem(BaseModel):
    id: CRMProvider
    name: str
    auth_type: Literal["oauth", "api_key", "password"]
    status: Literal["available", "connected"] = "available"


class CRMConnectionCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    provider: CRMProvider = Field(validation_alias=AliasChoices("provider", "crmId", "crm_id"))
    workspace_name: str = Field(
        min_length=1,
        max_length=255,
        validation_alias=AliasChoices("workspace_name", "workspaceName", "workspace", "clientName"),
    )
    login_email: EmailStr = Field(validation_alias=AliasChoices("login_email", "loginEmail", "email", "username"))
    credential: str = Field(
        min_length=1,
        description="OAuth code, API key, password, or access token.",
        validation_alias=AliasChoices("credential", "secret", "loginSecret", "password", "apiKey", "token"),
    )
    sync_scope: SyncScope = Field(default="contacts", validation_alias=AliasChoices("sync_scope", "syncScope", "scope"))
    allow_collab: bool = Field(default=True, validation_alias=AliasChoices("allow_collab", "allowCollab", "enableCollaboration"))
    auto_sync: bool = Field(default=True, validation_alias=AliasChoices("auto_sync", "autoSync", "enableAutoSync"))


class CRMConnectionUpdate(BaseModel):
    workspace_name: str | None = Field(default=None, max_length=255)
    login_email: EmailStr | None = None
    credential: str | None = None
    sync_scope: SyncScope | None = None
    allow_collab: bool | None = None
    auto_sync: bool | None = None
    status: Literal["connected", "disconnected", "expired", "error"] | None = None


class CRMConnectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    provider: str
    workspace_name: str
    login_email: EmailStr
    sync_scope: str
    allow_collab: bool
    auto_sync: bool
    status: str
    created_at: datetime
    updated_at: datetime


class CRMConnectionStatus(BaseModel):
    provider: str
    status: str
    connected: bool
    workspace_name: str | None = None
    sync_scope: str | None = None
