import uuid

from app.modules.companies.exceptions import InvalidOwnerReference
from app.modules.companies.schemas import (
    CompanyCreate,
    CompanyListResponse,
    CompanyResponse,
    CompanySummary,
    CompanyUpdate,
)
from app.modules.companies.service import CompanyService
from app.shared.contracts.auth_contract import AuthContractProtocol
from app.shared.contracts.geo_contract import GeoContractProtocol


class CompanyUseCase:
    """Implements CompanyContractProtocol. Entry point for the companies module —
    both its own router and other modules (e.g. contacts, for company_id
    validation) call in through here, never through CompanyService directly.
    Depends on AuthContractProtocol (not the concrete auth module) to validate
    an owner_id reference, and on GeoContractProtocol to validate the
    country/state/city location (issue #26)."""

    def __init__(
        self, service: CompanyService, auth: AuthContractProtocol, geo: GeoContractProtocol
    ) -> None:
        self._service = service
        self._auth = auth
        self._geo = geo

    async def _validate_owner_id(self, tenant_id: uuid.UUID, owner_id: str | None) -> None:
        if owner_id is None:
            return
        if not await self._auth.user_exists(tenant_id, uuid.UUID(owner_id)):
            raise InvalidOwnerReference()

    @staticmethod
    def _safe_uuid(value: str | None) -> uuid.UUID | None:
        # `value` may come from the currently-stored row (see
        # update_company's merge below), which can still hold pre-#26
        # free-text state/city on rows nobody has re-saved yet. A malformed
        # value can never come from the payload itself — CompanyUpdate's own
        # validators already reject a non-UUID state/city with a 422 before
        # this is reached — so treat it as "no location on file" rather than
        # raising, or every PATCH to a legacy row would 500.
        if value is None:
            return None
        try:
            return uuid.UUID(value)
        except ValueError:
            return None

    async def _validate_location(
        self, country: str | None, state: str | None, city: str | None
    ) -> None:
        await self._geo.validate_location(
            country,
            self._safe_uuid(state),
            self._safe_uuid(city),
        )

    async def create_company(
        self, tenant_id: uuid.UUID, actor_id: uuid.UUID, payload: CompanyCreate
    ) -> CompanyResponse:
        await self._validate_owner_id(tenant_id, payload.owner_id)
        await self._validate_location(payload.country, payload.state, payload.city)
        return await self._service.create_company(tenant_id, actor_id, payload)

    async def get_company(
        self, tenant_id: uuid.UUID, company_id: uuid.UUID
    ) -> CompanyResponse:
        return await self._service.get_company(tenant_id, company_id)

    async def company_exists(self, tenant_id: uuid.UUID, company_id: uuid.UUID) -> bool:
        return await self._service.company_exists(tenant_id, company_id)

    async def list_companies(
        self,
        tenant_id: uuid.UUID,
        page: int,
        page_size: int,
        *,
        status: str | None = None,
        company_type: str | None = None,
        size: str | None = None,
        industry: str | None = None,
        owner_id: uuid.UUID | None = None,
        q: str | None = None,
        sort: str = "created_at",
        order: str = "desc",
    ) -> CompanyListResponse:
        return await self._service.list_companies(
            tenant_id,
            page,
            page_size,
            status=status,
            company_type=company_type,
            size=size,
            industry=industry,
            owner_id=owner_id,
            q=q,
            sort=sort,
            order=order,
        )

    async def update_company(
        self,
        tenant_id: uuid.UUID,
        company_id: uuid.UUID,
        actor_id: uuid.UUID,
        payload: CompanyUpdate,
    ) -> CompanyResponse:
        if "owner_id" in payload.model_fields_set:
            await self._validate_owner_id(tenant_id, payload.owner_id)
        if payload.model_fields_set & {"country", "state", "city"}:
            # country/state/city are a cascading triple (state requires
            # country, city requires state) — a PATCH touching only one of
            # them must be validated against the *effective* location
            # (payload overrides merged onto the currently-stored values),
            # not the payload in isolation, or e.g. "PATCH {state: X}" on a
            # company that already has a country would incorrectly 422.
            current = await self._service.get_company(tenant_id, company_id)
            country = (
                payload.country if "country" in payload.model_fields_set else current.country
            )
            state = payload.state if "state" in payload.model_fields_set else current.state
            city = payload.city if "city" in payload.model_fields_set else current.city
            await self._validate_location(country, state, city)
        return await self._service.update_company(tenant_id, company_id, actor_id, payload)

    async def delete_company(self, tenant_id: uuid.UUID, company_id: uuid.UUID) -> None:
        await self._service.delete_company(tenant_id, company_id)

    async def search_companies(
        self, tenant_id: uuid.UUID, query: str, limit: int = 20
    ) -> list[CompanySummary]:
        return await self._service.search_companies(tenant_id, query, limit)

    async def lookup_companies(
        self, tenant_id: uuid.UUID, ids: list[uuid.UUID]
    ) -> list[CompanySummary]:
        return await self._service.lookup_companies(tenant_id, ids)
