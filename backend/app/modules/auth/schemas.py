import re
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

_RESERVED_SLUGS = {"www", "api", "app", "admin", "mail", "pranata", "static", "assets"}


class RegisterTenantRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    organization_name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=3, max_length=63)
    industry: str | None = None
    team_size: str | None = None

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        v = v.strip()
        if v != v.lower():
            raise ValueError("Slug must be lowercase")
        v = v.lower()
        if not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{1,61}[a-z0-9])?", v):
            raise ValueError("Slug must be lowercase alphanumeric with hyphens, 3-63 chars")
        if v in _RESERVED_SLUGS:
            raise ValueError("Slug is reserved and cannot be used")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not any(c.isdigit() for c in v) or not any(c.isalpha() for c in v):
            raise ValueError("Password must contain at least one letter and one digit")
        return v


class CreateUserRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role_id: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not any(c.isdigit() for c in v) or not any(c.isalpha() for c in v):
            raise ValueError("Password must contain at least one letter and one digit")
        return v


class InviteUserRequest(BaseModel):
    email: EmailStr
    full_name: str | None = None
    role_id: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class AcceptInviteRequest(BaseModel):
    token: str
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not any(c.isdigit() for c in v) or not any(c.isalpha() for c in v):
            raise ValueError("Password must contain at least one letter and one digit")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


# ── Responses ─────────────────────────────────────────────────────────────────

class AuthUserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    suite_role: str


class RegisterTenantResponse(BaseModel):
    tenant_id: str
    slug: str
    user: AuthUserResponse


class InviteSentResponse(BaseModel):
    message: str = "Invitation sent successfully."


class MeResponse(BaseModel):
    id: str
    email: str
    full_name: str
    suite_role: str
    tenant_id: str
    is_active: bool
    created_at: datetime
