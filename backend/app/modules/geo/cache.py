"""Redis per-scope cache for geo reference data (issue #26).

Strategy: cache-aside, keyed by parent scope (not one raw blob, not
per-search-term) — see issue #26 "Redis caching strategy" for the rationale.
Keys are version-prefixed so the whole shape can be busted by bumping
``_VERSION``. Freshness comes from write-through invalidation on admin writes
(``invalidate_states`` / ``invalidate_cities`` / ``invalidate_countries``,
called by GeoService after every admin mutation) — the TTL below is a long
safety net only, not the mechanism that keeps the cache correct.
"""
import json
import uuid

from redis.asyncio import Redis

_VERSION = "v1"
_COUNTRIES_KEY = f"geo:{_VERSION}:countries"
# Safety net only (see module docstring) — not how freshness is achieved.
_SAFETY_TTL_SECONDS = 7 * 24 * 60 * 60


def _states_key(country_code: str) -> str:
    return f"geo:{_VERSION}:states:{country_code.upper()}"


def _cities_key(state_id: uuid.UUID | str) -> str:
    return f"geo:{_VERSION}:cities:{state_id}"


class GeoCache:
    """Thin wrapper around Redis for the geo module's cache-aside reads.

    Kept as its own class (rather than inline redis calls in GeoService) so
    tests can mock cache behavior directly instead of needing a real Redis
    client wired through ``request.app.state.redis``.
    """

    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def get_countries(self) -> list[dict] | None:
        return await self._get_json(_COUNTRIES_KEY)

    async def set_countries(self, items: list[dict]) -> None:
        await self._set_json(_COUNTRIES_KEY, items)

    async def invalidate_countries(self) -> None:
        await self._redis.delete(_COUNTRIES_KEY)

    async def get_states(self, country_code: str) -> list[dict] | None:
        return await self._get_json(_states_key(country_code))

    async def set_states(self, country_code: str, items: list[dict]) -> None:
        await self._set_json(_states_key(country_code), items)

    async def invalidate_states(self, country_code: str) -> None:
        await self._redis.delete(_states_key(country_code))

    async def get_cities(self, state_id: uuid.UUID | str) -> list[dict] | None:
        return await self._get_json(_cities_key(state_id))

    async def set_cities(self, state_id: uuid.UUID | str, items: list[dict]) -> None:
        await self._set_json(_cities_key(state_id), items)

    async def invalidate_cities(self, state_id: uuid.UUID | str) -> None:
        await self._redis.delete(_cities_key(state_id))

    async def _get_json(self, key: str) -> list[dict] | None:
        raw = await self._redis.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (TypeError, ValueError):
            # Corrupt/unexpected cache content — treat as a miss rather than
            # 500ing the request; the caller will repopulate from Postgres.
            return None

    async def _set_json(self, key: str, items: list[dict]) -> None:
        await self._redis.set(key, json.dumps(items), ex=_SAFETY_TTL_SECONDS)
