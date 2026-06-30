from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.models
from app.config import settings
from app.database import Base, engine
from app.routers import crm, crm_auth, crm_sync, crm_webhooks


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description="Backend API for connecting and syncing multiple CRM providers.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(crm.router)
    app.include_router(crm_auth.router)
    app.include_router(crm_auth.alias_router)
    app.include_router(crm_sync.router)
    app.include_router(crm_webhooks.router)

    @app.get("/health", tags=["health"])
    def health_check():
        return {"status": "healthy", "service": settings.app_name}

    return app


Base.metadata.create_all(bind=engine)
app = create_app()
