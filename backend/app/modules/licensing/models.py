import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base import Base, AuditMixin, TimestampMixin, UUIDMixin
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


class Permission(Base, UUIDMixin):
    """Per-app permission catalog. Global — no RLS."""
    __tablename__ = "permissions"

    app_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()"
    )

    __table_args__ = (
        UniqueConstraint("app_id", "code", name="uq_permissions_app_code"),
        Index("ix_permissions_app_id", "app_id"),
    )


class Role(Base, UUIDMixin, TimestampMixin, AuditMixin):
    """Per-app role. tenant_id=NULL means global system role. RLS: tenant match OR NULL."""
    __tablename__ = "roles"

    tenant_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    app_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    __table_args__ = (
        Index("ix_roles_tenant_id", "tenant_id"),
        Index("ix_roles_app_id", "app_id"),
    )


class RolePermission(Base, UUIDMixin):
    """Many-to-many: role ↔ permission."""
    __tablename__ = "role_permissions"

    role_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    permission_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()"
    )

    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permissions_pair"),
        Index("ix_role_permissions_role_id", "role_id"),
        Index("ix_role_permissions_permission_id", "permission_id"),
    )


class UserRole(Base, UUIDMixin):
    """Role assignment — bound to an app_seat, not directly to a user. RLS on tenant_id."""
    __tablename__ = "user_roles"

    tenant_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    app_seat_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    role_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()"
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("app_seat_id", "role_id", name="uq_user_roles_seat_role"),
        Index("ix_user_roles_tenant_id", "tenant_id"),
        Index("ix_user_roles_app_seat_id", "app_seat_id"),
        Index("ix_user_roles_role_id", "role_id"),
    )
