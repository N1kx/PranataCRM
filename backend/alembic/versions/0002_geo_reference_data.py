"""geo reference data — geo_countries / geo_states / geo_cities (no RLS, global)

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-16

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── geo_countries ─────────────────────────────────────────────────────────
    # Global reference data (ISO 3166-1) — deliberately NO tenant_id / RLS, a
    # documented exception to ADR-002 (RLS applies to tenant business data,
    # not platform reference data shared by every tenant). See issue #26.
    op.create_table(
        "geo_countries",
        sa.Column("code", sa.String(2), primary_key=True),
        sa.Column("name_en", sa.String(100), nullable=False),
        sa.Column("name_id", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
    )

    # ── geo_states ────────────────────────────────────────────────────────────
    op.create_table(
        "geo_states",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("country_code", sa.String(2), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("code", sa.String(20), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("country_code", "name", name="uq_geo_states_country_name"),
    )
    op.create_index("ix_geo_states_country_code", "geo_states", ["country_code"])

    # ── geo_cities ────────────────────────────────────────────────────────────
    op.create_table(
        "geo_cities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("state_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("country_code", sa.String(2), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("state_id", "name", name="uq_geo_cities_state_name"),
    )
    op.create_index("ix_geo_cities_state_id", "geo_cities", ["state_id"])
    op.create_index("ix_geo_cities_country_code", "geo_cities", ["country_code"])

    # ── seed data ─────────────────────────────────────────────────────────────
    # Countries (full ISO 3166-1 alpha-2 set) + Indonesia provinces/cities are
    # seeded by a plain, idempotent SQL script (db/seed/geo_reference_data.sql),
    # run via `psql` from entrypoint.sh right after `alembic upgrade head` — not
    # embedded in this migration, so the (large, occasionally-revised) reference
    # data can be updated/re-run on every deploy without a new schema migration
    # each time. See that file's header comment.


def downgrade() -> None:
    op.drop_table("geo_cities")
    op.drop_table("geo_states")
    op.drop_table("geo_countries")
