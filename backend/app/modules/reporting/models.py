import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base import Base, UUIDMixin
from app.shared.types import uuid7


class ReportSnapshot(Base, UUIDMixin):
    """Pre-computed KPI aggregations per tenant + report type + period. RLS on tenant_id."""
    __tablename__ = "report_snapshots"

    tenant_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)
    period: Mapped[str] = mapped_column(String(30), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()"
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "report_type", "period",
            name="uq_report_snapshots_tenant_type_period",
        ),
        Index("ix_report_snapshots_tenant_id", "tenant_id"),
        Index("ix_report_snapshots_report_type", "report_type"),
    )
