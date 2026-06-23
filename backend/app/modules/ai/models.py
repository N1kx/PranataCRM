import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base import AuditMixin, Base, TimestampMixin, UUIDMixin
from app.shared.types import AgentType, AITaskStatus, KnowledgeSourceType, TriggerType

# pgvector import — optional at import time; fails gracefully if extension not installed.
try:
    from pgvector.sqlalchemy import Vector
    _VECTOR_AVAILABLE = True
except ImportError:
    _VECTOR_AVAILABLE = False


class AITask(Base, UUIDMixin, TimestampMixin, AuditMixin):
    """AI agent work item + HITL approval state. RLS on tenant_id."""
    __tablename__ = "ai_tasks"

    tenant_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    contact_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    deal_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)

    agent_type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default=AITaskStatus.PENDING)
    trigger_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default=TriggerType.SYSTEM
    )
    input_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    output_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "agent_type IN ('followup','scorer','summarizer','chatbot')",
            name="ck_ai_tasks_agent_type",
        ),
        CheckConstraint(
            "status IN ('pending','awaiting_approval','approved','rejected','done','failed')",
            name="ck_ai_tasks_status",
        ),
        CheckConstraint(
            "trigger_type IN ('manual','system','scheduled')",
            name="ck_ai_tasks_trigger_type",
        ),
        Index("ix_ai_tasks_tenant_id", "tenant_id"),
        Index("ix_ai_tasks_contact_id", "contact_id"),
        Index("ix_ai_tasks_deal_id", "deal_id"),
        Index("ix_ai_tasks_approved_by", "approved_by"),
        Index("ix_ai_tasks_agent_type", "agent_type"),
        Index("ix_ai_tasks_status", "status"),
    )


def _build_knowledge_base_class():
    """Returns KnowledgeBase model with vector column if pgvector is available."""
    extra_cols: dict = {}
    if _VECTOR_AVAILABLE:
        extra_cols["embedding"] = mapped_column(Vector(1536), nullable=True)

    attrs = {
        "__tablename__": "knowledge_base",
        "tenant_id": mapped_column(PGUUID(as_uuid=True), nullable=False),
        "title": mapped_column(String(255), nullable=False),
        "content": mapped_column(Text, nullable=False),
        "source_type": mapped_column(
            String(20), nullable=False, default=KnowledgeSourceType.MANUAL
        ),
        "source_url": mapped_column(Text, nullable=True),
        "__table_args__": (
            CheckConstraint(
                "source_type IN ('file','url','manual')",
                name="ck_knowledge_base_source_type",
            ),
            Index("ix_knowledge_base_tenant_id", "tenant_id"),
        ),
        **extra_cols,
    }
    return type(
        "KnowledgeBase",
        (Base, UUIDMixin, TimestampMixin, AuditMixin),
        attrs,
    )


KnowledgeBase = _build_knowledge_base_class()
