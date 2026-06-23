import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base import AuditMixin, Base, TimestampMixin, UUIDMixin
from app.shared.types import BillingPlan, SuiteRole


class Tenant(Base, UUIDMixin, TimestampMixin):
    """Root table — one row per organization. No RLS (it IS the root)."""
    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    plan: Mapped[str] = mapped_column(String(20), nullable=False, default=BillingPlan.FREE)
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    subscription_status: Mapped[str | None] = mapped_column(String(50), default="active")
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    settings: Mapped[dict] = mapped_column(JSONB, default=dict)

    __table_args__ = (
        UniqueConstraint("slug", name="uq_tenants_slug"),
    )


class User(Base, UUIDMixin, TimestampMixin):
    """User identity at the suite level. RLS on tenant_id."""
    __tablename__ = "users"

    tenant_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(Text, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    suite_role: Mapped[str] = mapped_column(
        String(20), nullable=False, default=SuiteRole.MEMBER
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
        Index("ix_users_tenant_id", "tenant_id"),
    )


class RefreshToken(Base, UUIDMixin):
    """JWT refresh tokens. No updated_at — tokens are write-once."""
    __tablename__ = "refresh_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    token_hash: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    ip_address: Mapped[str | None] = mapped_column(INET, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()"
    )

    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_refresh_tokens_hash"),
        Index("ix_refresh_tokens_user_id", "user_id"),
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
