from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.crm_connection import CRMConnection
from app.schemas.crm_connection import CRMCatalogItem, CRMConnectionCreate, CRMConnectionRead
from app.services.crm.crm_factory import CRMFactory
from app.services.token_service import TokenService


router = APIRouter(prefix="/api/crm", tags=["crm"])
token_service = TokenService()

CRM_PROVIDER_REGISTRY: list[CRMCatalogItem] = [
    CRMCatalogItem(id="salesforce", name="Salesforce", auth_type="oauth"),
    CRMCatalogItem(id="hubspot", name="HubSpot CRM", auth_type="oauth"),
    CRMCatalogItem(id="zoho", name="Zoho CRM", auth_type="oauth"),
    CRMCatalogItem(id="pipedrive", name="Pipedrive", auth_type="api_key"),
    CRMCatalogItem(id="microsoft_d365", name="Microsoft D365", auth_type="oauth"),
    CRMCatalogItem(id="freshsales", name="Freshsales", auth_type="api_key"),
    CRMCatalogItem(id="copper", name="Copper CRM", auth_type="api_key"),
    CRMCatalogItem(id="insightly", name="Insightly CRM", auth_type="api_key"),
    CRMCatalogItem(id="keap", name="Keap", auth_type="oauth"),
]


@router.get("/providers", response_model=list[CRMCatalogItem])
def list_crm_providers(db: Session = Depends(get_db)):
    connected = {row.provider for row in db.query(CRMConnection).filter(CRMConnection.status == "connected").all()}
    return [
        item.model_copy(update={"status": "connected" if item.id in connected else "available"})
        for item in CRM_PROVIDER_REGISTRY
    ]


@router.get("/connections", response_model=list[CRMConnectionRead])
def list_connections(db: Session = Depends(get_db)):
    return db.query(CRMConnection).order_by(CRMConnection.created_at.desc()).all()


@router.get("/connections/{provider}", response_model=CRMConnectionRead)
def get_connection(provider: str, db: Session = Depends(get_db)):
    connection = db.query(CRMConnection).filter(CRMConnection.provider == provider).first()
    if not connection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CRM connection not found")
    return connection


def save_connection(payload: CRMConnectionCreate, db: Session, encrypted_refresh_token: str | None = None):
    encrypted_token = token_service.encrypt_token(payload.credential)
    connection = db.query(CRMConnection).filter(CRMConnection.provider == payload.provider).first()

    if connection:
        connection.workspace_name = payload.workspace_name
        connection.login_email = str(payload.login_email)
        connection.encrypted_access_token = encrypted_token
        connection.encrypted_refresh_token = encrypted_refresh_token
        connection.sync_scope = payload.sync_scope
        connection.allow_collab = payload.allow_collab
        connection.auto_sync = payload.auto_sync
        connection.status = "connected"
    else:
        connection = CRMConnection(
            provider=payload.provider,
            workspace_name=payload.workspace_name,
            login_email=str(payload.login_email),
            encrypted_access_token=encrypted_token,
            encrypted_refresh_token=encrypted_refresh_token,
            sync_scope=payload.sync_scope,
            allow_collab=payload.allow_collab,
            auto_sync=payload.auto_sync,
            status="connected",
        )
        db.add(connection)

    db.commit()
    db.refresh(connection)
    return connection


@router.post("/connections", response_model=CRMConnectionRead, status_code=status.HTTP_201_CREATED)
async def create_or_update_connection(payload: CRMConnectionCreate, db: Session = Depends(get_db)):
    client = CRMFactory.create(payload.provider, access_token=payload.credential, api_key=payload.credential)
    try:
        await client.test_connection()
    except NotImplementedError as exc:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(exc)) from exc

    return save_connection(payload, db)


@router.delete("/connections/{provider}")
def delete_connection(provider: str, db: Session = Depends(get_db)):
    connection = db.query(CRMConnection).filter(CRMConnection.provider == provider).first()
    if not connection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CRM connection not found")

    db.delete(connection)
    db.commit()
    return {"message": f"{provider} disconnected"}
