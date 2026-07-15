import uuid

from sqlalchemy import CheckConstraint, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base import AuditMixin, Base, TimestampMixin, UUIDMixin
from app.shared.types import CompanyType


class Company(Base, UUIDMixin, TimestampMixin, AuditMixin):
    """Company/account record. RLS on tenant_id."""
    __tablename__ = "companies"

    tenant_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    owner_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    legal_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    website: Mapped[str | None] = mapped_column(Text, nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    size: Mapped[str | None] = mapped_column(String(20), nullable=True)
    employee_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    company_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default=CompanyType.PROSPECT
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    arr: Mapped[float | None] = mapped_column(nullable=True)
    annual_revenue: Mapped[float | None] = mapped_column(nullable=True)
    source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    address_line1: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address_line2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    twitter_handle: Mapped[str | None] = mapped_column(String(100), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list] = mapped_column(JSONB, default=list)
    custom_fields: Mapped[dict] = mapped_column(JSONB, default=dict)

    __table_args__ = (
        CheckConstraint(
            "company_type IN ('prospect','customer','partner','vendor','competitor','other')",
            name="ck_companies_type",
        ),
        CheckConstraint("status IN ('active','inactive')", name="ck_companies_status"),
        CheckConstraint(
            "size IN ('1-10','11-50','51-200','201-500','500+') OR size IS NULL",
            name="ck_companies_size",
        ),
        Index("ix_companies_tenant_id", "tenant_id"),
        Index("ix_companies_owner_id", "owner_id"),
        Index("ix_companies_company_type", "company_type"),
        Index("ix_companies_status", "status"),
    )
