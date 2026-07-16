"""One-off, idempotent backfill: map existing free-text contacts/companies
``country``/``city`` values to the structured geo references introduced by
issue #26 (ISO alpha-2 country codes, geo_states/geo_cities ids).

Run with: `python -m scripts.backfill_geo_locations` (from backend/, same
environment as the app/Alembic). Safe to re-run: only rows whose current
``country`` value is NOT already a 2-letter code get touched, so a second run
is a no-op for anything already migrated (either by this script or by a
normal PATCH through the new API).

Scope (best-effort, per issue #26's "Data migration / backfill" section):
- ``country``: matched case-insensitively against ISO English names and a
  short list of common aliases (e.g. "USA", "United States" -> "US").
- ``city``: matched case-insensitively against ``geo_cities.name`` *within
  the row's resolved country* (so "Bandung" only matches Indonesia's
  Bandung), and only after country resolved successfully.
- ``state``: NOT attempted — free-text province/state names are far more
  ambiguous to match confidently than city names, and the existing `state`
  column was barely populated to begin with (issue #26 background). Left
  as-is; admins can fill it in per-record via the UI's location picker.

Rows that can't be confidently mapped are logged (with their id and the
original value) and left completely untouched — never dropped, never
guessed. Re-run after adding aliases to ``_COUNTRY_ALIASES`` or after the geo
city dataset grows to pick up previously-unmatched rows.
"""
import asyncio

from sqlalchemy import select

from app.database import AsyncSessionFactory
from app.modules.companies.models import Company
from app.modules.contacts.models import Contact
from app.modules.geo.models import GeoCity, GeoCountry
from app.shared.logging import configure_logging, get_logger

logger = get_logger(__name__)

# Common non-ISO-name spellings seen in free-text data -> ISO alpha-2.
_COUNTRY_ALIASES: dict[str, str] = {
    "usa": "US", "u.s.a.": "US", "u.s.": "US", "united states of america": "US",
    "uk": "GB", "u.k.": "GB", "great britain": "GB", "england": "GB",
    "uae": "AE",
    "indo": "ID", "republic of indonesia": "ID",
    "south korea": "KR", "korea": "KR",
    "north korea": "KP",
    "russia": "RU",
    "vietnam": "VN",
    "laos": "LA",
    "syria": "SY",
    "burma": "MM",
}


def _looks_like_iso_code(value: str) -> bool:
    return len(value) == 2 and value.isalpha()


async def _build_country_lookup(session) -> dict[str, str]:
    """{lowercased name/alias: ISO code} for every seeded country, plus the
    hand-maintained alias table above."""
    result = await session.execute(select(GeoCountry.code, GeoCountry.name_en))
    lookup = {name.lower(): code for code, name in result.all()}
    lookup.update(_COUNTRY_ALIASES)
    return lookup


async def _build_city_lookup(session, country_code: str) -> dict[str, str]:
    result = await session.execute(
        select(GeoCity.id, GeoCity.name).where(GeoCity.country_code == country_code)
    )
    return {name.lower(): str(city_id) for city_id, name in result.all()}


async def _backfill_model(session, model, label: str) -> None:
    country_lookup = await _build_country_lookup(session)
    city_cache: dict[str, dict[str, str]] = {}

    result = await session.execute(
        select(model.id, model.country, model.city).where(model.country.is_not(None))
    )
    rows = result.all()

    matched_country = matched_city = unmatched = 0
    for row_id, country_raw, city_raw in rows:
        country_value = (country_raw or "").strip()
        if not country_value or _looks_like_iso_code(country_value):
            continue  # already migrated or empty — idempotent skip

        iso_code = country_lookup.get(country_value.lower())
        if iso_code is None:
            unmatched += 1
            logger.warning(
                "geo_backfill_unmatched_country",
                model=label, row_id=str(row_id), value=country_raw,
            )
            continue

        update_values: dict = {"country": iso_code}

        city_value = (city_raw or "").strip()
        if city_value:
            if iso_code not in city_cache:
                city_cache[iso_code] = await _build_city_lookup(session, iso_code)
            city_id = city_cache[iso_code].get(city_value.lower())
            if city_id is not None:
                update_values["city"] = city_id
                matched_city += 1
            else:
                # Country resolved but city didn't — clear nothing, leave the
                # free-text city as-is for manual cleanup (it would otherwise
                # fail the new UUID-format validation on the next PATCH that
                # doesn't touch this field, but that's fine: unset fields are
                # never revalidated, per ContactUpdate/CompanyUpdate semantics).
                logger.info(
                    "geo_backfill_unmatched_city",
                    model=label, row_id=str(row_id), country=iso_code, value=city_raw,
                )

        await session.execute(
            model.__table__.update().where(model.id == row_id).values(**update_values)
        )
        matched_country += 1

    logger.info(
        "geo_backfill_model_complete",
        model=label, rows_seen=len(rows), country_matched=matched_country,
        city_matched=matched_city, unmatched=unmatched,
    )


async def run() -> None:
    # Deliberately cross-tenant: this operator script queries every tenant's
    # rows directly (no `app.current_tenant_id` session var), matching how
    # the rest of this codebase currently connects — the app DB role is the
    # table owner, which bypasses RLS by default in Postgres; nothing in
    # app/ sets that session var yet (RLS policies exist per ADR-002 but
    # aren't wired to a live session context). Not this script's gap to fix.
    async with AsyncSessionFactory() as session:
        await _backfill_model(session, Contact, "contacts")
        await _backfill_model(session, Company, "companies")
        await session.commit()


if __name__ == "__main__":
    configure_logging()
    asyncio.run(run())
