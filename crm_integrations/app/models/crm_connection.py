from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CRMConnection(Base):
    __tablename__ = "crm_connections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    provider: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    account_id: Mapped[int | None] = mapped_column(ForeignKey("crm_accounts.id"), nullable=True)
    workspace_name: Mapped[str] = mapped_column(String(255), nullable=False)
    login_email: Mapped[str] = mapped_column(String(255), nullable=False)
    encrypted_access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    encrypted_refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sync_scope: Mapped[str] = mapped_column(String(50), default="contacts", nullable=False)
    allow_collab: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    auto_sync: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="connected", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    account = relationship("CRMAccount", back_populates="connections")
