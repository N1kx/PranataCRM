import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint, Date, DateTime, Index,
    Integer, Numeric, String, Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base import AuditMixin, Base, TimestampMixin, UUIDMixin
from app.shared.types import DealStage, DealStatus, DealType, Priority


class Deal(Base, UUIDMixin, TimestampMixin, AuditMixin):
    """Sales deal/opportunity. RLS on tenant_id."""
    __tablename__ = "deals"

    tenant_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    contact_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    company_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    owner_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    stage: Mapped[str] = mapped_column(String(20), nullable=False, default=DealStage.LEAD)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=DealStatus.OPEN)
    deal_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    value: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="IDR")
    probability: Mapped[int] = mapped_column(Integer, default=0)
    weighted_value: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    expected_close_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    actual_close_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    stage_changed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    priority: Mapped[str | None] = mapped_column(String(10), nullable=True)
    source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    next_step: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_step_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    competitor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    close_reason: Mapped[str | None] = mapped_column(String(100), nullable=True)
    lost_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ai_score_signals: Mapped[dict] = mapped_column(JSONB, default=dict)
    ai_score_reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_scored_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    tags: Mapped[list] = mapped_column(JSONB, default=list)
    custom_fields: Mapped[dict] = mapped_column(JSONB, default=dict)

    __table_args__ = (
        CheckConstraint(
            "stage IN ('lead','qualified','proposal','won','lost')",
            name="ck_deals_stage",
        ),
        CheckConstraint(
            "status IN ('open','won','lost','abandoned')",
            name="ck_deals_status",
        ),
        CheckConstraint(
            "deal_type IN ('new_business','renewal','upsell','expansion','cross_sell') OR deal_type IS NULL",
            name="ck_deals_deal_type",
        ),
        CheckConstraint(
            "priority IN ('low','medium','high') OR priority IS NULL",
            name="ck_deals_priority",
        ),
        CheckConstraint("probability BETWEEN 0 AND 100", name="ck_deals_probability"),
        CheckConstraint(
            "ai_score BETWEEN 0 AND 100 OR ai_score IS NULL",
            name="ck_deals_ai_score",
        ),
        Index("ix_deals_tenant_id", "tenant_id"),
        Index("ix_deals_contact_id", "contact_id"),
        Index("ix_deals_company_id", "company_id"),
        Index("ix_deals_owner_id", "owner_id"),
        Index("ix_deals_stage", "stage"),
        Index("ix_deals_status", "status"),
    )
