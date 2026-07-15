import uuid

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.shared.types import CompanySize, CompanyType

_ALLOWED_COMPANY_TYPE = {t.value for t in CompanyType}
_ALLOWED_SIZE = {s.value for s in CompanySize}
_ALLOWED_STATUS = {"active", "inactive"}

# Allowlists for GET /companies query params — never interpolate raw client
# input into the query. Keys are the client-facing values; values are the
# matching Company model column names.
ALLOWED_SORT_FIELDS = {
    "created_at": "created_at",
    "name": "name",
    "company_type": "company_type",
    "status": "status",
    "employee_count": "employee_count",
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


class _CompanyFieldsMixin(BaseModel):
    owner_id: str | None = None
    legal_name: str | None = Field(default=None, max_length=255)
    domain: str | None = Field(default=None, max_length=255)
    website: str | None = None
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    industry: str | None = Field(default=None, max_length=100)
    size: str | None = None
    employee_count: int | None = Field(default=None, ge=0)
    company_type: str | None = None
    status: str | None = None
    arr: float | None = None
    annual_revenue: float | None = None
    source: str | None = Field(default=None, max_length=50)
    address_line1: str | None = Field(default=None, max_length=255)
    address_line2: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    postal_code: str | None = Field(default=None, max_length=20)
    country: str | None = Field(default=None, max_length=100)
    timezone: str | None = Field(default=None, max_length=50)
    linkedin_url: str | None = None
    twitter_handle: str | None = Field(default=None, max_length=100)
    logo_url: str | None = None
    description: str | None = None
    tags: list[str] | None = None
    custom_fields: dict | None = None

    @field_validator(
        "owner_id", "legal_name", "domain", "website", "phone", "industry",
        "source", "address_line1", "address_line2", "city", "state",
        "postal_code", "country", "timezone", "linkedin_url", "twitter_handle",
        "logo_url", "description",
        mode="before",
    )
    @classmethod
    def _trim_strings(cls, v: str | None) -> str | None:
        return _trim(v)

    @field_validator("email", mode="before")
    @classmethod
    def _lowercase_email(cls, v: str | None) -> str | None:
        # EmailStr already enforces the RFC 5321 254-char limit, which is within
        # the DB column size (String(255)), so no explicit max_length is needed.
        trimmed = _trim(v)
        return trimmed.lower() if trimmed else None

    @field_validator("company_type", mode="before")
    @classmethod
    def _validate_company_type(cls, v: str | None) -> str:
        # company_type is NOT NULL in the DB — an explicit null must 422, not 500.
        _reject_null("company_type", v)
        if v not in _ALLOWED_COMPANY_TYPE:
            raise ValueError(
                f"company_type must be one of: {', '.join(sorted(_ALLOWED_COMPANY_TYPE))}."
            )
        return v

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

    @field_validator("size")
    @classmethod
    def _validate_size(cls, v: str | None) -> str | None:
        if v is not None and v not in _ALLOWED_SIZE:
            raise ValueError(
                f"size must be one of: {', '.join(sorted(_ALLOWED_SIZE))}."
            )
        return v

    @field_validator("tags", "custom_fields", mode="before")
    @classmethod
    def _reject_null_containers(cls, v, info):
        # tags/custom_fields are NOT NULL in the DB — reject explicit null.
        return _reject_null(info.field_name, v)

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


class CompanyCreate(_CompanyFieldsMixin):
    # name/phone/country are optional at the DB/model level (unchanged), but
    # required specifically on create so every new company has a minimum
    # useful profile — enforced here, not via a schema change.
    name: str = Field(min_length=1, max_length=255)
    phone: str = Field(min_length=1, max_length=50)
    country: str = Field(min_length=1, max_length=100)

    @field_validator("name", mode="before")
    @classmethod
    def _trim_name(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip()
        if not v:
            raise ValueError("name must be between 1 and 255 characters.")
        return v

    @field_validator("phone", mode="before")
    @classmethod
    def _trim_required_phone(cls, v: str) -> str:
        _reject_null("phone", v)
        v = v.strip() if isinstance(v, str) else v
        if not v:
            raise ValueError("phone is required.")
        return v

    @field_validator("country", mode="before")
    @classmethod
    def _trim_required_country(cls, v: str) -> str:
        _reject_null("country", v)
        v = v.strip() if isinstance(v, str) else v
        if not v:
            raise ValueError("country is required.")
        return v


class CompanyUpdate(_CompanyFieldsMixin):
    # name/phone/country stay mandatory on update too: omitting them from a
    # PATCH is fine (partial update, these validators don't run for unset
    # fields), but sending an explicit null or blank string to clear one of
    # them is rejected — a company may never end up without a name/phone/country.
    name: str | None = Field(default=None, min_length=1, max_length=255)
    phone: str | None = Field(default=None, min_length=1, max_length=50)
    country: str | None = Field(default=None, min_length=1, max_length=100)

    @field_validator("name", mode="before")
    @classmethod
    def _trim_name(cls, v: str | None) -> str:
        # name is NOT NULL in the DB. Omitting it is fine (this validator does
        # not run for unset fields), but an explicit null must 422.
        _reject_null("name", v)
        v = v.strip() if isinstance(v, str) else v
        if not v:
            raise ValueError("name must be between 1 and 255 characters.")
        return v

    @field_validator("phone", mode="before")
    @classmethod
    def _trim_required_phone(cls, v: str | None) -> str:
        _reject_null("phone", v)
        v = v.strip() if isinstance(v, str) else v
        if not v:
            raise ValueError("phone is required.")
        return v

    @field_validator("country", mode="before")
    @classmethod
    def _trim_required_country(cls, v: str | None) -> str:
        _reject_null("country", v)
        v = v.strip() if isinstance(v, str) else v
        if not v:
            raise ValueError("country is required.")
        return v


class CompanyResponse(BaseModel):
    id: str
    tenant_id: str
    owner_id: str | None
    name: str
    legal_name: str | None
    domain: str | None
    website: str | None
    email: str | None
    phone: str | None
    industry: str | None
    size: str | None
    employee_count: int | None
    company_type: str
    status: str
    arr: float | None
    annual_revenue: float | None
    source: str | None
    address_line1: str | None
    address_line2: str | None
    city: str | None
    state: str | None
    postal_code: str | None
    country: str | None
    timezone: str | None
    linkedin_url: str | None
    twitter_handle: str | None
    logo_url: str | None
    description: str | None
    tags: list[str]
    custom_fields: dict
    created_at: str
    updated_at: str


class CompanyListResponse(BaseModel):
    items: list[CompanyResponse]
    total: int
    page: int
    page_size: int


class CompanySummary(BaseModel):
    """Lightweight shape for the company_id autocomplete picker (search/lookup)."""
    id: str
    name: str
    domain: str | None = None
