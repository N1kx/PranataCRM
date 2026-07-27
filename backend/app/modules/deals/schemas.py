import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.shared.types import DealStage, DealStatus, DealType, Priority

_ALLOWED_DEAL_TYPE = {t.value for t in DealType}
_ALLOWED_PRIORITY = {p.value for p in Priority}
_ALLOWED_STAGE = {s.value for s in DealStage}
_ALLOWED_STATUS = {s.value for s in DealStatus}

# Allowlist for GET /deals query params — never interpolate raw client
# input into the query. Keys are the client-facing values; values are the
# matching Deal model column names.
ALLOWED_SORT_FIELDS = {
    "created_at": "created_at",
    "title": "title",
    "value": "value",
    "expected_close_date": "expected_close_date",
    "probability": "probability",
    "stage": "stage",
    "status": "status",
}


def _trim(v: str | None) -> str | None:
    if v is None:
        return None
    v = v.strip()
    return v or None


def _reject_null(field_name: str, value):
    """Reject an explicitly-sent ``null`` for a DB-non-nullable field.

    In Pydantic v2 a field_validator does not run for omitted fields (defaults
    are not validated), so this only fires when the client sends an explicit
    ``null`` — turning a would-be 500 (NOT NULL violation / response crash)
    into a clean 422.
    """
    if value is None:
        raise ValueError(f"{field_name} may not be null.")
    return value


class _DealFieldsMixin(BaseModel):
    description: str | None = None
    contact_id: str | None = None
    company_id: str | None = None
    owner_id: str | None = None
    deal_type: str | None = None
    value: Decimal | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    probability: int | None = Field(default=None, ge=0, le=100)
    priority: str | None = None
    source: str | None = Field(default=None, max_length=50)
    next_step: str | None = None
    next_step_date: date | None = None
    competitor: str | None = Field(default=None, max_length=255)
    tags: list[str] | None = None
    custom_fields: dict | None = None

    @field_validator(
        "description", "contact_id", "company_id", "owner_id",
        "source", "next_step", "competitor",
        mode="before",
    )
    @classmethod
    def _trim_strings(cls, v: str | None) -> str | None:
        return _trim(v)

    @field_validator("value", "probability", mode="before")
    @classmethod
    def _reject_null_numeric(cls, v, info):
        # value/probability map to NOT NULL columns with server defaults —
        # omitting them is fine (this validator doesn't run for unset fields),
        # but an explicit null must 422 rather than crash the weighted_value
        # computation (None * Decimal) or the NOT NULL insert.
        return _reject_null(info.field_name, v)

    @field_validator("currency", mode="before")
    @classmethod
    def _normalize_currency(cls, v: str | None) -> str | None:
        # currency is NOT NULL and "cannot be cleared" (issue #36) — reject an
        # explicit null before trimming/normalizing.
        _reject_null("currency", v)
        v = _trim(v)
        if v is None:
            return None
        v = v.upper()
        if len(v) != 3 or not v.isalpha():
            raise ValueError("currency must be a 3-letter ISO 4217 code (e.g. IDR, USD).")
        return v

    @field_validator("contact_id")
    @classmethod
    def _validate_contact_id(cls, v: str | None) -> str | None:
        if v is None:
            return None
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError("contact_id must be a valid UUID.")
        return v

    @field_validator("company_id")
    @classmethod
    def _validate_company_id(cls, v: str | None) -> str | None:
        if v is None:
            return None
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError("company_id must be a valid UUID.")
        return v

    @field_validator("owner_id")
    @classmethod
    def _validate_owner_id(cls, v: str | None) -> str | None:
        if v is None:
            return None
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError("owner_id must be a valid UUID.")
        return v

    @field_validator("deal_type")
    @classmethod
    def _validate_deal_type(cls, v: str | None) -> str | None:
        if v is not None and v not in _ALLOWED_DEAL_TYPE:
            raise ValueError(
                f"deal_type must be one of: {', '.join(sorted(_ALLOWED_DEAL_TYPE))}."
            )
        return v

    @field_validator("priority")
    @classmethod
    def _validate_priority(cls, v: str | None) -> str | None:
        if v is not None and v not in _ALLOWED_PRIORITY:
            raise ValueError(
                f"priority must be one of: {', '.join(sorted(_ALLOWED_PRIORITY))}."
            )
        return v

    @field_validator("tags", "custom_fields", mode="before")
    @classmethod
    def _reject_null_containers(cls, v, info):
        # tags/custom_fields are NOT NULL in the DB — reject explicit null.
        return _reject_null(info.field_name, v)


class DealCreate(_DealFieldsMixin):
    title: str = Field(min_length=1, max_length=255)
    # expected_close_date is nullable at the DB/model level (unchanged), but
    # required specifically on create — same business-rule-not-migration
    # pattern as CompanyCreate.country.
    expected_close_date: date
    # owner_id is nullable at the DB/model level (unchanged; still unlinkable
    # via PATCH — see DealUpdate) but required on create so every new deal has
    # an accountable owner from the start — same pattern as expected_close_date.
    owner_id: str
    # stage defaults to 'lead' on create; not accepted at all on update —
    # PATCH /deals/{id}/stage is the only way to change it afterwards.
    stage: str | None = None

    @field_validator("title", mode="before")
    @classmethod
    def _trim_title(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip()
        if not v:
            raise ValueError("title must be between 1 and 255 characters.")
        return v

    @field_validator("owner_id", mode="before")
    @classmethod
    def _require_owner_id(cls, v: str | None) -> str:
        v = _trim(v) if isinstance(v, str) else v
        if not v:
            raise ValueError("owner_id is required.")
        return v

    @field_validator("stage", mode="before")
    @classmethod
    def _validate_stage(cls, v: str | None) -> str | None:
        if v is not None and v not in _ALLOWED_STAGE:
            raise ValueError(f"stage must be one of: {', '.join(sorted(_ALLOWED_STAGE))}.")
        return v


class DealUpdate(_DealFieldsMixin):
    # title stays mandatory on update too: omitting it from a PATCH is fine
    # (partial update, this validator doesn't run for unset fields), but
    # sending an explicit null or blank string to clear it is rejected.
    title: str | None = Field(default=None, min_length=1, max_length=255)
    # expected_close_date cannot be cleared once set — explicit null -> 422.
    expected_close_date: date | None = None
    # stage/status are accepted here only so DealUseCase can detect that the
    # client tried to set them and reject with a clear, dedicated error
    # (INVALID_STAGE_TRANSITION) instead of a generic validation failure —
    # see DealUseCase.update_deal. They are never applied to the row from
    # this endpoint.
    stage: str | None = None
    status: str | None = None

    @field_validator("title", mode="before")
    @classmethod
    def _trim_title(cls, v: str | None) -> str:
        # title is NOT NULL in the DB. Omitting it is fine (this validator
        # does not run for unset fields), but an explicit null must 422.
        _reject_null("title", v)
        v = v.strip() if isinstance(v, str) else v
        if not v:
            raise ValueError("title must be between 1 and 255 characters.")
        return v

    @field_validator("expected_close_date", mode="before")
    @classmethod
    def _reject_null_expected_close_date(cls, v):
        return _reject_null("expected_close_date", v)

    @field_validator("owner_id", mode="before")
    @classmethod
    def _reject_null_owner_id(cls, v):
        # A deal must always have an accountable owner, so unlike company_id /
        # contact_id (optional soft references that may be unlinked), owner_id
        # can be reassigned but never cleared. Omitting it from a PATCH is
        # still fine — this validator does not run for unset fields.
        return _reject_null("owner_id", v)

    @field_validator("status", mode="before")
    @classmethod
    def _validate_status(cls, v):
        # A garbage status is a plain field-validation error (like deal_type/
        # priority), NOT an INVALID_STAGE_TRANSITION. The open<->abandoned
        # transition rules for valid values are enforced in the service.
        v = _reject_null("status", _trim(v) if isinstance(v, str) else v)
        if v not in _ALLOWED_STATUS:
            raise ValueError(
                f"status must be one of: {', '.join(sorted(_ALLOWED_STATUS))}."
            )
        return v


class DealStageUpdate(BaseModel):
    stage: str
    close_reason: str | None = Field(default=None, max_length=100)
    lost_reason: str | None = None

    @field_validator("stage", mode="before")
    @classmethod
    def _validate_stage(cls, v: str) -> str:
        _reject_null("stage", v)
        if v not in _ALLOWED_STAGE:
            raise ValueError(f"stage must be one of: {', '.join(sorted(_ALLOWED_STAGE))}.")
        return v

    @field_validator("close_reason", "lost_reason", mode="before")
    @classmethod
    def _trim_strings(cls, v: str | None) -> str | None:
        return _trim(v)


class DealResponse(BaseModel):
    id: str
    tenant_id: str
    contact_id: str | None
    company_id: str | None
    owner_id: str | None
    title: str
    description: str | None
    stage: str
    status: str
    deal_type: str | None
    value: Decimal
    currency: str
    probability: int
    weighted_value: Decimal | None
    expected_close_date: date | None
    actual_close_date: date | None
    stage_changed_at: str | None
    priority: str | None
    source: str | None
    next_step: str | None
    next_step_date: date | None
    competitor: str | None
    close_reason: str | None
    lost_reason: str | None
    tags: list[str]
    custom_fields: dict
    created_at: str
    updated_at: str


class DealListResponse(BaseModel):
    items: list[DealResponse]
    total: int
    page: int
    page_size: int
