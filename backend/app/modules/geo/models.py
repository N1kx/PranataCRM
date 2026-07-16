import uuid

from sqlalchemy import Boolean, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base import Base, TimestampMixin, UUIDMixin


class GeoCountry(Base):
    """ISO 3166-1 alpha-2 country reference. Effectively read-only (seeded once).

    Global reference data, shared by every tenant — deliberately has NO
    tenant_id and NO RLS policy (documented exception to ADR-002: RLS applies
    to tenant business data, not platform reference data). See issue #26.
    """
    __tablename__ = "geo_countries"

    code: Mapped[str] = mapped_column(String(2), primary_key=True)
    name_en: Mapped[str] = mapped_column(String(100), nullable=False)
    name_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class GeoState(Base, UUIDMixin, TimestampMixin):
    """State / province / first-level administrative division.

    Admin-editable (unlike countries) because administrative regions change —
    Indonesia in particular splits provinces regularly. Global reference data:
    no tenant_id, no RLS. Soft reference to geo_countries.code (ADR-005, no FK).
    """
    __tablename__ = "geo_states"

    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    __table_args__ = (
        Index("ix_geo_states_country_code", "country_code"),
        UniqueConstraint("country_code", "name", name="uq_geo_states_country_name"),
    )


class GeoCity(Base, UUIDMixin, TimestampMixin):
    """City / regency (kota / kabupaten).

    Admin-editable, same rationale as GeoState. Global reference data: no
    tenant_id, no RLS. Soft references to geo_states.id and (denormalized,
    for direct country->city queries) geo_countries.code (ADR-005, no FK).
    """
    __tablename__ = "geo_cities"

    state_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    __table_args__ = (
        Index("ix_geo_cities_state_id", "state_id"),
        Index("ix_geo_cities_country_code", "country_code"),
        UniqueConstraint("state_id", "name", name="uq_geo_cities_state_name"),
    )
