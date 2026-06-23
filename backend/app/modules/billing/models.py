import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base import Base, UUIDMixin
from app.shared.types import WebhookStatus


class Webhook(Base, UUIDMixin):
    """Incoming webhook event log (e.g. Stripe). RLS optional."""
    __tablename__ = "webhooks"

    tenant_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=WebhookStatus.PENDING)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()"
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending','processed','failed')",
            name="ck_webhooks_status",
        ),
        Index("ix_webhooks_tenant_id", "tenant_id"),
        Index("ix_webhooks_event_type", "event_type"),
        Index("ix_webhooks_status", "status"),
    )
