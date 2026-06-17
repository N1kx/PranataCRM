from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass(frozen=True)
class DomainEvent:
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ── Contact events ────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ContactCreated(DomainEvent):
    contact_id: UUID | None = None


@dataclass(frozen=True)
class ContactUpdated(DomainEvent):
    contact_id: UUID | None = None


# ── Deal events ───────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class DealStageChanged(DomainEvent):
    deal_id: UUID | None = None
    old_stage: str = ""
    new_stage: str = ""


# ── Auth events ───────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class UserLoggedIn(DomainEvent):
    user_id: UUID | None = None
