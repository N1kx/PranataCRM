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


class CompanyUseCase:
    """Implements CompanyContractProtocol. Entry point for the companies module —
    both its own router and other modules (e.g. contacts, for company_id
    validation) call in through here, never through CompanyService directly.
    Depends on AuthContractProtocol (not the concrete auth module) to validate
    an owner_id reference."""

    def __init__(self, service: CompanyService, auth: AuthContractProtocol) -> None:
        self._service = service
        self._auth = auth

    async def _validate_owner_id(self, tenant_id: uuid.UUID, owner_id: str | None) -> None:
        if owner_id is None:
            return
        if not await self._auth.user_exists(tenant_id, uuid.UUID(owner_id)):
            raise InvalidOwnerReference()

    async def create_company(
        self, tenant_id: uuid.UUID, actor_id: uuid.UUID, payload: CompanyCreate
    ) -> CompanyResponse:
        await self._validate_owner_id(tenant_id, payload.owner_id)
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
