import uuid

from app.modules.deals.exceptions import (
    InvalidCompanyReference,
    InvalidContactReference,
    InvalidOwnerReference,
)
from app.modules.deals.schemas import (
    DealCreate,
    DealListResponse,
    DealResponse,
    DealStageUpdate,
    DealUpdate,
)
from app.modules.deals.service import DealService
from app.shared.contracts.auth_contract import AuthContractProtocol
from app.shared.contracts.company_contract import CompanyContractProtocol
from app.shared.contracts.contact_contract import ContactContractProtocol


class DealUseCase:
    """Implements DealContractProtocol. Entry point for the deals module —
    its router calls in through here, never through DealService directly.
    Depends on AuthContractProtocol / CompanyContractProtocol /
    ContactContractProtocol (not the concrete auth/companies/contacts
    modules) to validate owner_id/company_id/contact_id references
    (ADR-005 write guard) — never via direct import of those modules."""

    def __init__(
        self,
        service: DealService,
        auth: AuthContractProtocol,
        companies: CompanyContractProtocol,
        contacts: ContactContractProtocol,
    ) -> None:
        self._service = service
        self._auth = auth
        self._companies = companies
        self._contacts = contacts

    async def _validate_owner_id(self, tenant_id: uuid.UUID, owner_id: str | None) -> None:
        if owner_id is None:
            return
        if not await self._auth.user_exists(tenant_id, uuid.UUID(owner_id)):
            raise InvalidOwnerReference()

    async def _validate_company_id(self, tenant_id: uuid.UUID, company_id: str | None) -> None:
        if company_id is None:
            return
        if not await self._companies.company_exists(tenant_id, uuid.UUID(company_id)):
            raise InvalidCompanyReference()

    async def _validate_contact_id(self, tenant_id: uuid.UUID, contact_id: str | None) -> None:
        if contact_id is None:
            return
        if not await self._contacts.contact_exists(tenant_id, uuid.UUID(contact_id)):
            raise InvalidContactReference()

    async def create_deal(
        self, tenant_id: uuid.UUID, actor_id: uuid.UUID, payload: DealCreate
    ) -> DealResponse:
        await self._validate_owner_id(tenant_id, payload.owner_id)
        await self._validate_company_id(tenant_id, payload.company_id)
        await self._validate_contact_id(tenant_id, payload.contact_id)
        return await self._service.create_deal(tenant_id, actor_id, payload)

    async def get_deal(self, tenant_id: uuid.UUID, deal_id: uuid.UUID) -> DealResponse:
        return await self._service.get_deal(tenant_id, deal_id)

    async def deal_exists(self, tenant_id: uuid.UUID, deal_id: uuid.UUID) -> bool:
        return await self._service.deal_exists(tenant_id, deal_id)

    async def list_deals(
        self,
        tenant_id: uuid.UUID,
        page: int,
        page_size: int,
        *,
        stage: str | None = None,
        status: str | None = None,
        deal_type: str | None = None,
        priority: str | None = None,
        owner_id: uuid.UUID | None = None,
        contact_id: uuid.UUID | None = None,
        company_id: uuid.UUID | None = None,
        q: str | None = None,
        sort: str = "created_at",
        order: str = "desc",
    ) -> DealListResponse:
        return await self._service.list_deals(
            tenant_id,
            page,
            page_size,
            stage=stage,
            status=status,
            deal_type=deal_type,
            priority=priority,
            owner_id=owner_id,
            contact_id=contact_id,
            company_id=company_id,
            q=q,
            sort=sort,
            order=order,
        )

    async def update_deal(
        self,
        tenant_id: uuid.UUID,
        deal_id: uuid.UUID,
        actor_id: uuid.UUID,
        payload: DealUpdate,
    ) -> DealResponse:
        # owner_id/company_id/contact_id are only present in model_fields_set
        # when the client sent them explicitly (not merely defaulted to
        # None) — this lets a partial PATCH omit any of them entirely
        # without triggering validation, while still validating an explicit
        # non-null value or skipping an explicit null (unlink).
        if "owner_id" in payload.model_fields_set:
            await self._validate_owner_id(tenant_id, payload.owner_id)
        if "company_id" in payload.model_fields_set:
            await self._validate_company_id(tenant_id, payload.company_id)
        if "contact_id" in payload.model_fields_set:
            await self._validate_contact_id(tenant_id, payload.contact_id)
        return await self._service.update_deal(tenant_id, deal_id, actor_id, payload)

    async def update_stage(
        self,
        tenant_id: uuid.UUID,
        deal_id: uuid.UUID,
        actor_id: uuid.UUID,
        payload: DealStageUpdate,
    ) -> DealResponse:
        return await self._service.update_stage(tenant_id, deal_id, actor_id, payload)

    async def delete_deal(self, tenant_id: uuid.UUID, deal_id: uuid.UUID) -> None:
        await self._service.delete_deal(tenant_id, deal_id)
