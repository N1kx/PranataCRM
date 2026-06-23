import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base import AuditMixin, Base, TimestampMixin, UUIDMixin
from app.shared.types import BillingPlan, SeatStatus, SubscriptionStatus


class App(Base, UUIDMixin):
    """Catalog of applications in Pranata Suites. Global — no RLS."""
    __tablename__ = "apps"

    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()"
    )

    __table_args__ = (
        UniqueConstraint("code", name="uq_apps_code"),
    )


class AppSubscription(Base, UUIDMixin, TimestampMixin, AuditMixin):
    """Tenant subscription to one app + purchased seat quota. RLS on tenant_id."""
    __tablename__ = "app_subscriptions"

    tenant_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    app_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    plan: Mapped[str] = mapped_column(String(20), nullable=False, default=BillingPlan.FREE)
    seats_purchased: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=SubscriptionStatus.ACTIVE
    )
    current_period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "app_id", name="uq_app_subscriptions_tenant_app"),
        Index("ix_app_subscriptions_tenant_id", "tenant_id"),
        Index("ix_app_subscriptions_app_id", "app_id"),
    )


class AppSeat(Base, UUIDMixin):
    """Which user occupies a seat in an app. RLS on tenant_id."""
    __tablename__ = "app_seats"

    tenant_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    subscription_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    app_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=SeatStatus.ACTIVE)
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()"
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("app_id", "user_id", name="uq_app_seats_app_user"),
        Index("ix_app_seats_tenant_id", "tenant_id"),
        Index("ix_app_seats_subscription_id", "subscription_id"),
        Index("ix_app_seats_app_id", "app_id"),
        Index("ix_app_seats_user_id", "user_id"),
    )


