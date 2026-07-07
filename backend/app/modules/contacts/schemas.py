import uuid

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.shared.types import ContactStatus, LifecycleStage, PreferredContactMethod

_ALLOWED_STATUS = {s.value for s in ContactStatus}
_ALLOWED_LIFECYCLE_STAGE = {s.value for s in LifecycleStage}
_ALLOWED_PREFERRED_CONTACT_METHOD = {s.value for s in PreferredContactMethod}


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


class _ContactFieldsMixin(BaseModel):
    last_name: str | None = Field(default=None, max_length=100)
    email: EmailStr | None = None
    secondary_email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    mobile_phone: str | None = Field(default=None, max_length=50)
    job_title: str | None = Field(default=None, max_length=255)
    department: str | None = Field(default=None, max_length=100)
    status: str | None = None
    lifecycle_stage: str | None = None
    lead_source: str | None = Field(default=None, max_length=50)
    preferred_contact_method: str | None = None
    preferred_language: str | None = Field(default=None, max_length=10)
    linkedin_url: str | None = Field(default=None, max_length=2048)
    company_id: str | None = None
    owner_id: str | None = None
    address_line1: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    postal_code: str | None = Field(default=None, max_length=20)
    country: str | None = Field(default=None, max_length=100)
    description: str | None = None
    tags: list[str] | None = None
    custom_fields: dict | None = None

    @field_validator(
        "last_name", "phone", "mobile_phone", "job_title", "department",
        "lead_source", "preferred_language", "linkedin_url",
        "address_line1", "city", "state", "postal_code", "country",
        "description", "company_id", "owner_id",
        mode="before",
    )
    @classmethod
    def _trim_strings(cls, v: str | None) -> str | None:
        return _trim(v)

    @field_validator("email", "secondary_email", mode="before")
    @classmethod
    def _lowercase_email(cls, v: str | None) -> str | None:
        trimmed = _trim(v)
        return trimmed.lower() if trimmed else None

    @field_validator("status", mode="before")
    @classmethod
    def _validate_status(cls, v: str | None) -> str:
        # status is NOT NULL in the DB — an explicit null must 422, not 500.
        _reject_null("status", v)
        if v not in _ALLOWED_STATUS:
            raise ValueError(
                f"status must be one of: {', '.join(sorted(_ALLOWED_STATUS))}."
            )
        return v

    @field_validator("tags", "custom_fields", mode="before")
    @classmethod
    def _reject_null_containers(cls, v, info):
        # tags/custom_fields are NOT NULL in the DB — reject explicit null.
        return _reject_null(info.field_name, v)

    @field_validator("lifecycle_stage")
    @classmethod
    def _validate_lifecycle_stage(cls, v: str | None) -> str | None:
        if v is not None and v not in _ALLOWED_LIFECYCLE_STAGE:
            raise ValueError(
                "lifecycle_stage must be one of: "
                f"{', '.join(sorted(_ALLOWED_LIFECYCLE_STAGE))}."
            )
        return v

    @field_validator("preferred_contact_method")
    @classmethod
    def _validate_preferred_contact_method(cls, v: str | None) -> str | None:
        if v is not None and v not in _ALLOWED_PREFERRED_CONTACT_METHOD:
            raise ValueError(
                "preferred_contact_method must be one of: "
                f"{', '.join(sorted(_ALLOWED_PREFERRED_CONTACT_METHOD))}."
            )
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


class ContactCreate(_ContactFieldsMixin):
    first_name: str = Field(min_length=1, max_length=100)

    @field_validator("first_name", mode="before")
    @classmethod
    def _trim_first_name(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip()
        if not v:
            raise ValueError("first_name must be between 1 and 100 characters.")
        return v


class ContactUpdate(_ContactFieldsMixin):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)

    @field_validator("first_name", mode="before")
    @classmethod
    def _trim_first_name(cls, v: str | None) -> str:
        # first_name is NOT NULL in the DB. Omitting it is fine (this validator
        # does not run for unset fields), but an explicit null must 422.
        _reject_null("first_name", v)
        v = v.strip() if isinstance(v, str) else v
        if not v:
            raise ValueError("first_name must be between 1 and 100 characters.")
        return v


class ContactResponse(BaseModel):
    id: str
    tenant_id: str
    owner_id: str | None
    company_id: str | None
    first_name: str
    last_name: str | None
    email: str | None
    secondary_email: str | None
    phone: str | None
    mobile_phone: str | None
    job_title: str | None
    department: str | None
    status: str
    lifecycle_stage: str | None
    lead_source: str | None
    linkedin_url: str | None
    twitter_handle: str | None
    address_line1: str | None
    city: str | None
    state: str | None
    postal_code: str | None
    country: str | None
    timezone: str | None
    preferred_contact_method: str | None
    preferred_language: str | None
    do_not_contact: bool
    description: str | None
    tags: list[str]
    custom_fields: dict
    created_at: str
    updated_at: str


class ContactListResponse(BaseModel):
    items: list[ContactResponse]
    total: int
    page: int
    page_size: int
