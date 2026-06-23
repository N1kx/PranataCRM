import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean, CheckConstraint, Date, DateTime, Index,
    Integer, String, Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base import AuditMixin, Base, TimestampMixin, UUIDMixin
from app.shared.types import (
    ActivityDirection, ActivityStatus, ActivityType,
    CompanySize, CompanyType, ContactStatus, LifecycleStage,
    PreferredContactMethod, Priority,
)


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


class Contact(Base, UUIDMixin, TimestampMixin, AuditMixin):
    """Individual contact record. RLS on tenant_id."""
    __tablename__ = "contacts"

    tenant_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    owner_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    company_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    secondary_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    mobile_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    job_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=ContactStatus.LEAD)
    lifecycle_stage: Mapped[str | None] = mapped_column(String(30), nullable=True)
    lead_source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    twitter_handle: Mapped[str | None] = mapped_column(String(100), nullable=True)
    address_line1: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    preferred_contact_method: Mapped[str | None] = mapped_column(String(20), nullable=True)
    preferred_language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    do_not_contact: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    birthday: Mapped[date | None] = mapped_column(Date, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list] = mapped_column(JSONB, default=list)
    custom_fields: Mapped[dict] = mapped_column(JSONB, default=dict)
    last_contacted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_activity_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('lead','qualified','customer','churned')",
            name="ck_contacts_status",
        ),
        CheckConstraint(
            "lifecycle_stage IN ('subscriber','lead','mql','sql','opportunity','customer','evangelist') OR lifecycle_stage IS NULL",
            name="ck_contacts_lifecycle_stage",
        ),
        CheckConstraint(
            "preferred_contact_method IN ('email','phone','sms','whatsapp') OR preferred_contact_method IS NULL",
            name="ck_contacts_preferred_contact_method",
        ),
        Index("ix_contacts_tenant_id", "tenant_id"),
        Index("ix_contacts_owner_id", "owner_id"),
        Index("ix_contacts_company_id", "company_id"),
        Index("ix_contacts_status", "status"),
        Index("ix_contacts_lifecycle_stage", "lifecycle_stage"),
    )


class Activity(Base, UUIDMixin, TimestampMixin, AuditMixin):
    """Activity timeline + tasks. type='task' doubles as a task/reminder. RLS on tenant_id."""
    __tablename__ = "activities"

    tenant_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    user_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    contact_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    company_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    deal_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)

    type: Mapped[str] = mapped_column(String(20), nullable=False)
    subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    direction: Mapped[str | None] = mapped_column(String(10), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ActivityStatus.COMPLETED
    )
    priority: Mapped[str | None] = mapped_column(String(10), nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    outcome: Mapped[str | None] = mapped_column(String(255), nullable=True)
    participants: Mapped[list] = mapped_column(JSONB, default=list)
    is_pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()"
    )

    __table_args__ = (
        CheckConstraint(
            "type IN ('email','call','note','meeting','deal_update','task','sms','whatsapp')",
            name="ck_activities_type",
        ),
        CheckConstraint(
            "status IN ('completed','scheduled','cancelled','pending')",
            name="ck_activities_status",
        ),
        CheckConstraint(
            "direction IN ('inbound','outbound') OR direction IS NULL",
            name="ck_activities_direction",
        ),
        CheckConstraint(
            "priority IN ('low','medium','high') OR priority IS NULL",
            name="ck_activities_priority",
        ),
        Index("ix_activities_tenant_id", "tenant_id"),
        Index("ix_activities_contact_id", "contact_id"),
        Index("ix_activities_company_id", "company_id"),
        Index("ix_activities_deal_id", "deal_id"),
        Index("ix_activities_user_id", "user_id"),
        Index("ix_activities_type", "type"),
        Index("ix_activities_status", "status"),
    )
