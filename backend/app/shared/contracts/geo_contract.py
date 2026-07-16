import uuid
from typing import Protocol, runtime_checkable

# GeoContractProtocol — the interface other modules (contacts, companies, ...)
# use to validate a country/state/city location without importing the geo
# module's internals. One domain-level method rather than three CRUD-style
# ones: callers have a (country, state, city) triple straight off their
# schema and want it validated as a unit — cross-parent consistency and
# cascade-completeness (state requires country, city requires state) are the
# geo module's rules to enforce, not each caller's. See issue #26.


@runtime_checkable
class GeoContractProtocol(Protocol):
    async def validate_location(
        self,
        country: str | None,
        state: uuid.UUID | None,
        city: uuid.UUID | None,
    ) -> None:
        """Validate a country/state/city combination for cross-module use.

        No-op if all three are None. Raises (from app.modules.geo.exceptions):
        - GeoValidationError (422, VALIDATION_ERROR) if `state` is given
          without `country`, or `city` without `state`.
        - InvalidCountryReference (422) if `country` isn't a known, active
          ISO 3166-1 alpha-2 code.
        - InvalidStateReference (422) if `state` doesn't belong to an active
          state under `country`.
        - InvalidCityReference (422) if `city` doesn't belong to an active
          city under `state`.
        """
        ...
