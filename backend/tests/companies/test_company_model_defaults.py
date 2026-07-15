import unittest

from app.modules.companies.models import Company
from app.shared.types import CompanyType


class CompanyModelDefaultsTests(unittest.TestCase):
    """CompanyResponse requires tags/custom_fields/company_type/status to be
    non-null. On create, the service omits these from the insert dict when the
    client didn't send them (payload.model_dump(exclude_unset=True)), relying
    on SQLAlchemy applying each column's ``default=`` at flush/INSERT time to
    fill them in (verified manually via Docker QA against Postgres — there is
    no sqlite/in-memory engine here since the model uses JSONB/PGUUID). This
    test guards the declarative side of that contract: if a future edit drops
    or changes one of these defaults, it fails here instead of only showing up
    as a NOT NULL violation / response-serialization 500 against a real DB."""

    def test_required_columns_declare_non_null_defaults(self) -> None:
        defaults = {
            column.name: column.default.arg
            for column in Company.__table__.columns
            if column.name in ("tags", "custom_fields", "company_type", "status")
        }

        # SQLAlchemy wraps a plain callable default to accept an ExecutionContext
        # arg (unused for a context-independent default like `list`/`dict`).
        self.assertEqual(defaults["tags"](None), [])
        self.assertEqual(defaults["custom_fields"](None), {})
        self.assertEqual(defaults["company_type"], CompanyType.PROSPECT)
        self.assertEqual(defaults["status"], "active")

        for column in Company.__table__.columns:
            if column.name in ("tags", "custom_fields", "company_type", "status"):
                self.assertFalse(
                    column.nullable, f"{column.name} must be NOT NULL to match CompanyResponse"
                )
