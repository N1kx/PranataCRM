"""initial schema — all tables + RLS policies

Revision ID: 0001
Revises:
Create Date: 2026-06-18

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Extensions ────────────────────────────────────────────────────────────
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # ── tenants ───────────────────────────────────────────────────────────────
    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("plan", sa.String(20), nullable=False, server_default="free"),
        sa.Column("stripe_customer_id", sa.String(255), nullable=True),
        sa.Column("subscription_status", sa.String(50), server_default="active"),
        sa.Column("trial_ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("settings", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("slug", name="uq_tenants_slug"),
    )

    # ── users ─────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.Text(), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column("suite_role", sa.String(20), nullable=False, server_default="member"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("suite_role IN ('tenant_owner','tenant_admin','member')", name="ck_users_suite_role"),
        sa.UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
    )
    op.create_index("ix_users_tenant_id", "users", ["tenant_id"])
    op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY tenant_isolation ON users "
        "USING (tenant_id = current_setting('app.current_tenant_id')::uuid);"
    )

    # ── refresh_tokens ────────────────────────────────────────────────────────
    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("token_hash", name="uq_refresh_tokens_hash"),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])

    # ── apps ──────────────────────────────────────────────────────────────────
    op.create_table(
        "apps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("code", name="uq_apps_code"),
    )

    # ── app_subscriptions ─────────────────────────────────────────────────────
    op.create_table(
        "app_subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("app_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("plan", sa.String(20), nullable=False, server_default="free"),
        sa.Column("seats_purchased", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("plan IN ('free','pro','enterprise')", name="ck_app_subscriptions_plan"),
        sa.CheckConstraint("status IN ('active','past_due','cancelled')", name="ck_app_subscriptions_status"),
        sa.UniqueConstraint("tenant_id", "app_id", name="uq_app_subscriptions_tenant_app"),
    )
    op.create_index("ix_app_subscriptions_tenant_id", "app_subscriptions", ["tenant_id"])
    op.create_index("ix_app_subscriptions_app_id", "app_subscriptions", ["app_id"])
    op.execute("ALTER TABLE app_subscriptions ENABLE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY tenant_isolation ON app_subscriptions "
        "USING (tenant_id = current_setting('app.current_tenant_id')::uuid);"
    )

    # ── app_seats ─────────────────────────────────────────────────────────────
    op.create_table(
        "app_seats",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subscription_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("app_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.CheckConstraint("status IN ('active','inactive')", name="ck_app_seats_status"),
        sa.UniqueConstraint("app_id", "user_id", name="uq_app_seats_app_user"),
    )
    op.create_index("ix_app_seats_tenant_id", "app_seats", ["tenant_id"])
    op.create_index("ix_app_seats_subscription_id", "app_seats", ["subscription_id"])
    op.create_index("ix_app_seats_app_id", "app_seats", ["app_id"])
    op.create_index("ix_app_seats_user_id", "app_seats", ["user_id"])
    op.execute("ALTER TABLE app_seats ENABLE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY tenant_isolation ON app_seats "
        "USING (tenant_id = current_setting('app.current_tenant_id')::uuid);"
    )

    # ── permissions ───────────────────────────────────────────────────────────
    op.create_table(
        "permissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("app_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(100), nullable=False),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("app_id", "code", name="uq_permissions_app_code"),
    )
    op.create_index("ix_permissions_app_id", "permissions", ["app_id"])

    # ── roles ─────────────────────────────────────────────────────────────────
    op.create_table(
        "roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("app_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_roles_tenant_id", "roles", ["tenant_id"])
    op.create_index("ix_roles_app_id", "roles", ["app_id"])
    op.execute("ALTER TABLE roles ENABLE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY tenant_or_global ON roles "
        "USING (tenant_id = current_setting('app.current_tenant_id')::uuid OR tenant_id IS NULL);"
    )

    # ── role_permissions ──────────────────────────────────────────────────────
    op.create_table(
        "role_permissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("permission_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("role_id", "permission_id", name="uq_role_permissions_pair"),
    )
    op.create_index("ix_role_permissions_role_id", "role_permissions", ["role_id"])
    op.create_index("ix_role_permissions_permission_id", "role_permissions", ["permission_id"])

    # ── user_roles ────────────────────────────────────────────────────────────
    op.create_table(
        "user_roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("app_seat_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.UniqueConstraint("app_seat_id", "role_id", name="uq_user_roles_seat_role"),
    )
    op.create_index("ix_user_roles_tenant_id", "user_roles", ["tenant_id"])
    op.create_index("ix_user_roles_app_seat_id", "user_roles", ["app_seat_id"])
    op.create_index("ix_user_roles_role_id", "user_roles", ["role_id"])
    op.execute("ALTER TABLE user_roles ENABLE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY tenant_isolation ON user_roles "
        "USING (tenant_id = current_setting('app.current_tenant_id')::uuid);"
    )

    # ── companies ─────────────────────────────────────────────────────────────
    op.create_table(
        "companies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("legal_name", sa.String(255), nullable=True),
        sa.Column("domain", sa.String(255), nullable=True),
        sa.Column("website", sa.Text(), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("industry", sa.String(100), nullable=True),
        sa.Column("size", sa.String(20), nullable=True),
        sa.Column("employee_count", sa.Integer(), nullable=True),
        sa.Column("company_type", sa.String(20), nullable=False, server_default="prospect"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("arr", sa.Numeric(15, 2), nullable=True),
        sa.Column("annual_revenue", sa.Numeric(18, 2), nullable=True),
        sa.Column("source", sa.String(50), nullable=True),
        sa.Column("address_line1", sa.String(255), nullable=True),
        sa.Column("address_line2", sa.String(255), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("state", sa.String(100), nullable=True),
        sa.Column("postal_code", sa.String(20), nullable=True),
        sa.Column("country", sa.String(100), nullable=True),
        sa.Column("timezone", sa.String(50), nullable=True),
        sa.Column("linkedin_url", sa.Text(), nullable=True),
        sa.Column("twitter_handle", sa.String(100), nullable=True),
        sa.Column("logo_url", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("tags", postgresql.JSONB(), server_default="[]"),
        sa.Column("custom_fields", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "company_type IN ('prospect','customer','partner','vendor','competitor','other')",
            name="ck_companies_type",
        ),
        sa.CheckConstraint("status IN ('active','inactive')", name="ck_companies_status"),
        sa.CheckConstraint(
            "size IN ('1-10','11-50','51-200','201-500','500+') OR size IS NULL",
            name="ck_companies_size",
        ),
    )
    op.create_index("ix_companies_tenant_id", "companies", ["tenant_id"])
    op.create_index("ix_companies_owner_id", "companies", ["owner_id"])
    op.create_index("ix_companies_company_type", "companies", ["company_type"])
    op.create_index("ix_companies_status", "companies", ["status"])
    op.execute("ALTER TABLE companies ENABLE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY tenant_isolation ON companies "
        "USING (tenant_id = current_setting('app.current_tenant_id')::uuid);"
    )

    # ── contacts ──────────────────────────────────────────────────────────────
    op.create_table(
        "contacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("secondary_email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("mobile_phone", sa.String(50), nullable=True),
        sa.Column("job_title", sa.String(255), nullable=True),
        sa.Column("department", sa.String(100), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="lead"),
        sa.Column("lifecycle_stage", sa.String(30), nullable=True),
        sa.Column("lead_source", sa.String(50), nullable=True),
        sa.Column("linkedin_url", sa.Text(), nullable=True),
        sa.Column("twitter_handle", sa.String(100), nullable=True),
        sa.Column("address_line1", sa.String(255), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("state", sa.String(100), nullable=True),
        sa.Column("postal_code", sa.String(20), nullable=True),
        sa.Column("country", sa.String(100), nullable=True),
        sa.Column("timezone", sa.String(50), nullable=True),
        sa.Column("preferred_contact_method", sa.String(20), nullable=True),
        sa.Column("preferred_language", sa.String(10), nullable=True),
        sa.Column("do_not_contact", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("birthday", sa.Date(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("tags", postgresql.JSONB(), server_default="[]"),
        sa.Column("custom_fields", postgresql.JSONB(), server_default="{}"),
        sa.Column("last_contacted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "status IN ('lead','qualified','customer','churned')",
            name="ck_contacts_status",
        ),
        sa.CheckConstraint(
            "lifecycle_stage IN ('subscriber','lead','mql','sql','opportunity','customer','evangelist') OR lifecycle_stage IS NULL",
            name="ck_contacts_lifecycle_stage",
        ),
        sa.CheckConstraint(
            "preferred_contact_method IN ('email','phone','sms','whatsapp') OR preferred_contact_method IS NULL",
            name="ck_contacts_preferred_contact_method",
        ),
    )
    op.create_index("ix_contacts_tenant_id", "contacts", ["tenant_id"])
    op.create_index("ix_contacts_owner_id", "contacts", ["owner_id"])
    op.create_index("ix_contacts_company_id", "contacts", ["company_id"])
    op.create_index("ix_contacts_status", "contacts", ["status"])
    op.create_index("ix_contacts_lifecycle_stage", "contacts", ["lifecycle_stage"])
    op.execute("ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY tenant_isolation ON contacts "
        "USING (tenant_id = current_setting('app.current_tenant_id')::uuid);"
    )

    # ── deals ─────────────────────────────────────────────────────────────────
    op.create_table(
        "deals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("contact_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("stage", sa.String(20), nullable=False, server_default="lead"),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("deal_type", sa.String(20), nullable=True),
        sa.Column("value", sa.Numeric(15, 2), server_default="0"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="IDR"),
        sa.Column("probability", sa.Integer(), server_default="0"),
        sa.Column("weighted_value", sa.Numeric(15, 2), nullable=True),
        sa.Column("expected_close_date", sa.Date(), nullable=True),
        sa.Column("actual_close_date", sa.Date(), nullable=True),
        sa.Column("stage_changed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("priority", sa.String(10), nullable=True),
        sa.Column("source", sa.String(50), nullable=True),
        sa.Column("next_step", sa.Text(), nullable=True),
        sa.Column("next_step_date", sa.Date(), nullable=True),
        sa.Column("competitor", sa.String(255), nullable=True),
        sa.Column("close_reason", sa.String(100), nullable=True),
        sa.Column("lost_reason", sa.Text(), nullable=True),
        sa.Column("ai_score", sa.Integer(), nullable=True),
        sa.Column("ai_score_signals", postgresql.JSONB(), server_default="{}"),
        sa.Column("ai_score_reasoning", sa.Text(), nullable=True),
        sa.Column("ai_scored_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tags", postgresql.JSONB(), server_default="[]"),
        sa.Column("custom_fields", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("stage IN ('lead','qualified','proposal','won','lost')", name="ck_deals_stage"),
        sa.CheckConstraint("status IN ('open','won','lost','abandoned')", name="ck_deals_status"),
        sa.CheckConstraint(
            "deal_type IN ('new_business','renewal','upsell','expansion','cross_sell') OR deal_type IS NULL",
            name="ck_deals_deal_type",
        ),
        sa.CheckConstraint("priority IN ('low','medium','high') OR priority IS NULL", name="ck_deals_priority"),
        sa.CheckConstraint("probability BETWEEN 0 AND 100", name="ck_deals_probability"),
        sa.CheckConstraint("ai_score BETWEEN 0 AND 100 OR ai_score IS NULL", name="ck_deals_ai_score"),
    )
    op.create_index("ix_deals_tenant_id", "deals", ["tenant_id"])
    op.create_index("ix_deals_contact_id", "deals", ["contact_id"])
    op.create_index("ix_deals_company_id", "deals", ["company_id"])
    op.create_index("ix_deals_owner_id", "deals", ["owner_id"])
    op.create_index("ix_deals_stage", "deals", ["stage"])
    op.create_index("ix_deals_status", "deals", ["status"])
    op.execute("ALTER TABLE deals ENABLE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY tenant_isolation ON deals "
        "USING (tenant_id = current_setting('app.current_tenant_id')::uuid);"
    )

    # ── activities ────────────────────────────────────────────────────────────
    op.create_table(
        "activities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("contact_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("deal_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("subject", sa.String(255), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("direction", sa.String(10), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="completed"),
        sa.Column("priority", sa.String(10), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("outcome", sa.String(255), nullable=True),
        sa.Column("participants", postgresql.JSONB(), server_default="[]"),
        sa.Column("is_pinned", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("metadata", postgresql.JSONB(), server_default="{}"),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "type IN ('email','call','note','meeting','deal_update','task','sms','whatsapp')",
            name="ck_activities_type",
        ),
        sa.CheckConstraint(
            "status IN ('completed','scheduled','cancelled','pending')",
            name="ck_activities_status",
        ),
        sa.CheckConstraint(
            "direction IN ('inbound','outbound') OR direction IS NULL",
            name="ck_activities_direction",
        ),
        sa.CheckConstraint(
            "priority IN ('low','medium','high') OR priority IS NULL",
            name="ck_activities_priority",
        ),
    )
    op.create_index("ix_activities_tenant_id", "activities", ["tenant_id"])
    op.create_index("ix_activities_contact_id", "activities", ["contact_id"])
    op.create_index("ix_activities_company_id", "activities", ["company_id"])
    op.create_index("ix_activities_deal_id", "activities", ["deal_id"])
    op.create_index("ix_activities_user_id", "activities", ["user_id"])
    op.create_index("ix_activities_type", "activities", ["type"])
    op.create_index("ix_activities_status", "activities", ["status"])
    op.execute("ALTER TABLE activities ENABLE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY tenant_isolation ON activities "
        "USING (tenant_id = current_setting('app.current_tenant_id')::uuid);"
    )

    # ── ai_tasks ──────────────────────────────────────────────────────────────
    op.create_table(
        "ai_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("contact_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("deal_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("agent_type", sa.String(20), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("trigger_type", sa.String(20), nullable=False, server_default="system"),
        sa.Column("input_data", postgresql.JSONB(), server_default="{}"),
        sa.Column("output_data", postgresql.JSONB(), server_default="{}"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "agent_type IN ('followup','scorer','summarizer','chatbot')",
            name="ck_ai_tasks_agent_type",
        ),
        sa.CheckConstraint(
            "status IN ('pending','awaiting_approval','approved','rejected','done','failed')",
            name="ck_ai_tasks_status",
        ),
        sa.CheckConstraint(
            "trigger_type IN ('manual','system','scheduled')",
            name="ck_ai_tasks_trigger_type",
        ),
    )
    op.create_index("ix_ai_tasks_tenant_id", "ai_tasks", ["tenant_id"])
    op.create_index("ix_ai_tasks_contact_id", "ai_tasks", ["contact_id"])
    op.create_index("ix_ai_tasks_deal_id", "ai_tasks", ["deal_id"])
    op.create_index("ix_ai_tasks_approved_by", "ai_tasks", ["approved_by"])
    op.create_index("ix_ai_tasks_agent_type", "ai_tasks", ["agent_type"])
    op.create_index("ix_ai_tasks_status", "ai_tasks", ["status"])
    op.execute("ALTER TABLE ai_tasks ENABLE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY tenant_isolation ON ai_tasks "
        "USING (tenant_id = current_setting('app.current_tenant_id')::uuid);"
    )

    # ── knowledge_base ────────────────────────────────────────────────────────
    op.create_table(
        "knowledge_base",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", sa.Text(), nullable=True),  # placeholder; real type set below
        sa.Column("source_type", sa.String(20), nullable=False, server_default="manual"),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "source_type IN ('file','url','manual')",
            name="ck_knowledge_base_source_type",
        ),
    )
    # Replace placeholder text column with the actual vector type
    op.execute("ALTER TABLE knowledge_base ALTER COLUMN embedding TYPE vector(1536) USING NULL::vector(1536);")
    op.create_index("ix_knowledge_base_tenant_id", "knowledge_base", ["tenant_id"])
    op.execute(
        "CREATE INDEX ix_knowledge_base_embedding ON knowledge_base "
        "USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);"
    )
    op.execute("ALTER TABLE knowledge_base ENABLE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY tenant_isolation ON knowledge_base "
        "USING (tenant_id = current_setting('app.current_tenant_id')::uuid);"
    )

    # ── webhooks ──────────────────────────────────────────────────────────────
    op.create_table(
        "webhooks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("status IN ('pending','processed','failed')", name="ck_webhooks_status"),
    )
    op.create_index("ix_webhooks_tenant_id", "webhooks", ["tenant_id"])
    op.create_index("ix_webhooks_event_type", "webhooks", ["event_type"])
    op.create_index("ix_webhooks_status", "webhooks", ["status"])

    # ── report_snapshots ──────────────────────────────────────────────────────
    op.create_table(
        "report_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("report_type", sa.String(50), nullable=False),
        sa.Column("period", sa.String(30), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint(
            "tenant_id", "report_type", "period",
            name="uq_report_snapshots_tenant_type_period",
        ),
    )
    op.create_index("ix_report_snapshots_tenant_id", "report_snapshots", ["tenant_id"])
    op.create_index("ix_report_snapshots_report_type", "report_snapshots", ["report_type"])
    op.execute("ALTER TABLE report_snapshots ENABLE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY tenant_isolation ON report_snapshots "
        "USING (tenant_id = current_setting('app.current_tenant_id')::uuid);"
    )


def downgrade() -> None:
    op.drop_table("report_snapshots")
    op.drop_table("webhooks")
    op.drop_table("knowledge_base")
    op.drop_table("ai_tasks")
    op.drop_table("activities")
    op.drop_table("deals")
    op.drop_table("contacts")
    op.drop_table("companies")
    op.drop_table("user_roles")
    op.drop_table("role_permissions")
    op.drop_table("roles")
    op.drop_table("permissions")
    op.drop_table("app_seats")
    op.drop_table("app_subscriptions")
    op.drop_table("apps")
    op.drop_table("refresh_tokens")
    op.drop_table("users")
    op.drop_table("tenants")
    op.execute("DROP EXTENSION IF EXISTS vector;")
