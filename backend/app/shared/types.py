import os
import time
import uuid
from enum import StrEnum


def uuid7() -> uuid.UUID:
    """
    UUID v7 (time-ordered) generated in the application layer.
    RFC 9562 layout: 48-bit ms timestamp | ver(7) | 12-bit rand_a |
    variant(0b10) | 62-bit rand_b.
    Compatible with PostgreSQL 15 (no DB function required).
    """
    unix_ms = int(time.time() * 1000) & ((1 << 48) - 1)
    rand = int.from_bytes(os.urandom(10), "big")
    value = unix_ms << 80
    value |= (0x7 << 76)
    value |= ((rand >> 68) & 0x0FFF) << 64
    value |= (0b10 << 62)
    value |= rand & ((1 << 62) - 1)
    return uuid.UUID(int=value)


# ── Suite-level role ──────────────────────────────────────────────────────────

class SuiteRole(StrEnum):
    TENANT_OWNER = "tenant_owner"
    TENANT_ADMIN = "tenant_admin"
    MEMBER = "member"


# ── Billing / plan ────────────────────────────────────────────────────────────

class BillingPlan(StrEnum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(StrEnum):
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"


class SeatStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


# ── Company / CRM ─────────────────────────────────────────────────────────────

class CompanyType(StrEnum):
    PROSPECT = "prospect"
    CUSTOMER = "customer"
    PARTNER = "partner"
    VENDOR = "vendor"
    COMPETITOR = "competitor"
    OTHER = "other"


class CompanySize(StrEnum):
    XS = "1-10"
    S = "11-50"
    M = "51-200"
    L = "201-500"
    XL = "500+"


# ── Contact ───────────────────────────────────────────────────────────────────

class ContactStatus(StrEnum):
    LEAD = "lead"
    QUALIFIED = "qualified"
    CUSTOMER = "customer"
    CHURNED = "churned"


class LifecycleStage(StrEnum):
    SUBSCRIBER = "subscriber"
    LEAD = "lead"
    MQL = "mql"
    SQL = "sql"
    OPPORTUNITY = "opportunity"
    CUSTOMER = "customer"
    EVANGELIST = "evangelist"


class PreferredContactMethod(StrEnum):
    EMAIL = "email"
    PHONE = "phone"
    SMS = "sms"
    WHATSAPP = "whatsapp"


# ── Deal ──────────────────────────────────────────────────────────────────────

class DealStage(StrEnum):
    LEAD = "lead"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    WON = "won"
    LOST = "lost"


class DealStatus(StrEnum):
    OPEN = "open"
    WON = "won"
    LOST = "lost"
    ABANDONED = "abandoned"


class DealType(StrEnum):
    NEW_BUSINESS = "new_business"
    RENEWAL = "renewal"
    UPSELL = "upsell"
    EXPANSION = "expansion"
    CROSS_SELL = "cross_sell"


class Priority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# ── Activity ──────────────────────────────────────────────────────────────────

class ActivityType(StrEnum):
    EMAIL = "email"
    CALL = "call"
    NOTE = "note"
    MEETING = "meeting"
    DEAL_UPDATE = "deal_update"
    TASK = "task"
    SMS = "sms"
    WHATSAPP = "whatsapp"


class ActivityStatus(StrEnum):
    COMPLETED = "completed"
    SCHEDULED = "scheduled"
    CANCELLED = "cancelled"
    PENDING = "pending"


class ActivityDirection(StrEnum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


# ── AI ────────────────────────────────────────────────────────────────────────

class AgentType(StrEnum):
    FOLLOWUP = "followup"
    SCORER = "scorer"
    SUMMARIZER = "summarizer"
    CHATBOT = "chatbot"


class AITaskStatus(StrEnum):
    PENDING = "pending"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    DONE = "done"
    FAILED = "failed"


class TriggerType(StrEnum):
    MANUAL = "manual"
    SYSTEM = "system"
    SCHEDULED = "scheduled"


class KnowledgeSourceType(StrEnum):
    FILE = "file"
    URL = "url"
    MANUAL = "manual"


# ── Webhook / billing ─────────────────────────────────────────────────────────

class WebhookStatus(StrEnum):
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"


# ── Notification ─────────────────────────────────────────────────────────────

class NotificationChannel(StrEnum):
    EMAIL = "email"
    IN_APP = "in_app"
