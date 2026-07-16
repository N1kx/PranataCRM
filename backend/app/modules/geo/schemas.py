from pydantic import BaseModel, Field, field_validator


def _trim(v: str | None) -> str | None:
    if v is None:
        return None
    v = v.strip()
    return v or None


def _reject_null(field_name: str, value):
    if value is None:
        raise ValueError(f"{field_name} may not be null.")
    return value


# ── Responses (also the shape cached in Redis — keep these flat/JSON-safe) ───

class GeoCountryResponse(BaseModel):
    code: str
    name_en: str
    name_id: str | None
    is_active: bool


class GeoStateResponse(BaseModel):
    id: str
    country_code: str
    name: str
    code: str | None
    is_active: bool


class GeoCityResponse(BaseModel):
    id: str
    state_id: str
    country_code: str
    name: str
    is_active: bool


# ── Admin write schemas ──────────────────────────────────────────────────────

class GeoStateCreate(BaseModel):
    country_code: str = Field(min_length=2, max_length=2)
    name: str = Field(min_length=1, max_length=100)
    code: str | None = Field(default=None, max_length=20)

    @field_validator("country_code", mode="before")
    @classmethod
    def _normalize_country_code(cls, v: str) -> str:
        _reject_null("country_code", v)
        v = v.strip().upper() if isinstance(v, str) else v
        if not v or len(v) != 2 or not v.isalpha():
            raise ValueError("country_code must be a 2-letter ISO 3166-1 alpha-2 code.")
        return v

    @field_validator("name", mode="before")
    @classmethod
    def _trim_name(cls, v: str) -> str:
        _reject_null("name", v)
        v = v.strip() if isinstance(v, str) else v
        if not v:
            raise ValueError("name must be between 1 and 100 characters.")
        return v

    @field_validator("code", mode="before")
    @classmethod
    def _trim_code(cls, v: str | None) -> str | None:
        return _trim(v)


class GeoStateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    code: str | None = Field(default=None, max_length=20)
    is_active: bool | None = None

    @field_validator("name", mode="before")
    @classmethod
    def _trim_name(cls, v: str | None) -> str:
        # name is NOT NULL in the DB. Omitting it is fine (this validator does
        # not run for unset fields), but an explicit null must 422.
        _reject_null("name", v)
        v = v.strip() if isinstance(v, str) else v
        if not v:
            raise ValueError("name must be between 1 and 100 characters.")
        return v

    @field_validator("code", mode="before")
    @classmethod
    def _trim_code(cls, v: str | None) -> str | None:
        return _trim(v)


class GeoCityCreate(BaseModel):
    state_id: str
    name: str = Field(min_length=1, max_length=100)

    @field_validator("state_id")
    @classmethod
    def _validate_state_id(cls, v: str) -> str:
        import uuid
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError("state_id must be a valid UUID.")
        return v

    @field_validator("name", mode="before")
    @classmethod
    def _trim_name(cls, v: str) -> str:
        _reject_null("name", v)
        v = v.strip() if isinstance(v, str) else v
        if not v:
            raise ValueError("name must be between 1 and 100 characters.")
        return v


class GeoCityUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    is_active: bool | None = None

    @field_validator("name", mode="before")
    @classmethod
    def _trim_name(cls, v: str | None) -> str:
        _reject_null("name", v)
        v = v.strip() if isinstance(v, str) else v
        if not v:
            raise ValueError("name must be between 1 and 100 characters.")
        return v


class GeoCountryUpdate(BaseModel):
    """Countries are ISO-fixed: no create/delete, only rename/activate."""
    name_en: str | None = Field(default=None, min_length=1, max_length=100)
    name_id: str | None = Field(default=None, max_length=100)
    is_active: bool | None = None

    @field_validator("name_en", mode="before")
    @classmethod
    def _trim_name_en(cls, v: str | None) -> str:
        _reject_null("name_en", v)
        v = v.strip() if isinstance(v, str) else v
        if not v:
            raise ValueError("name_en must be between 1 and 100 characters.")
        return v

    @field_validator("name_id", mode="before")
    @classmethod
    def _trim_name_id(cls, v: str | None) -> str | None:
        return _trim(v)
