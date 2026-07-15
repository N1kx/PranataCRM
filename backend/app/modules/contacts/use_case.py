import uuid

from app.modules.contacts.exceptions import InvalidCompanyReference, InvalidOwnerReference
from app.modules.contacts.schemas import (
    ContactCreate,
    ContactListResponse,
    ContactResponse,
    ContactUpdate,
)
from app.modules.contacts.service import ContactService
from app.shared.contracts.auth_contract import AuthContractProtocol
from app.shared.contracts.company_contract import CompanyContractProtocol


class ContactUseCase:
    """Entry point for the contacts module — its router calls in through here,
    never through ContactService directly. No other module currently consumes
    contacts data, so there is no ContactContractProtocol yet (see
    shared/contracts/contact_contract.py); this will implement it once one is
    needed. Depends on CompanyContractProtocol (not the concrete companies
    module) to validate a company_id reference, and on AuthContractProtocol
    to validate an owner_id reference."""

    def __init__(
        self,
        service: ContactService,
        companies: CompanyContractProtocol,
        auth: AuthContractProtocol,
    ) -> None:
        self._service = service
        self._companies = companies
        self._auth = auth

    async def _validate_company_id(self, tenant_id: uuid.UUID, company_id: str | None) -> None:
        if company_id is None:
            return
        if not await self._companies.company_exists(tenant_id, uuid.UUID(company_id)):
            raise InvalidCompanyReference()

    async def _validate_owner_id(self, tenant_id: uuid.UUID, owner_id: str | None) -> None:
        if owner_id is None:
            return
        if not await self._auth.user_exists(tenant_id, uuid.UUID(owner_id)):
            raise InvalidOwnerReference()

    async def create_contact(
        self, tenant_id: uuid.UUID, actor_id: uuid.UUID, payload: ContactCreate
    ) -> ContactResponse:
        await self._validate_company_id(tenant_id, payload.company_id)
        await self._validate_owner_id(tenant_id, payload.owner_id)
        return await self._service.create_contact(tenant_id, actor_id, payload)

    async def get_contact(
        self, tenant_id: uuid.UUID, contact_id: uuid.UUID
    ) -> ContactResponse:
        return await self._service.get_contact(tenant_id, contact_id)

    async def list_contacts(
        self,
        tenant_id: uuid.UUID,
        page: int,
        page_size: int,
        *,
        status: str | None = None,
        lifecycle_stage: str | None = None,
        owner_id: uuid.UUID | None = None,
        company_id: uuid.UUID | None = None,
        q: str | None = None,
        sort: str = "created_at",
        order: str = "desc",
    ) -> ContactListResponse:
        return await self._service.list_contacts(
            tenant_id,
            page,
            page_size,
            status=status,
            lifecycle_stage=lifecycle_stage,
            owner_id=owner_id,
            company_id=company_id,
            q=q,
            sort=sort,
            order=order,
        )

    async def update_contact(
        self,
        tenant_id: uuid.UUID,
        contact_id: uuid.UUID,
        actor_id: uuid.UUID,
        payload: ContactUpdate,
    ) -> ContactResponse:
        # company_id/owner_id are only present in model_fields_set when the
        # client sent them explicitly (not merely defaulted to None) — this is
        # what lets a partial PATCH omit either field entirely without
        # triggering validation, while still validating an explicit non-null
        # value or skipping an explicit null (unassign), matching
        # ContactUpdate's own semantics.
        if "company_id" in payload.model_fields_set:
            await self._validate_company_id(tenant_id, payload.company_id)
        if "owner_id" in payload.model_fields_set:
            await self._validate_owner_id(tenant_id, payload.owner_id)
        return await self._service.update_contact(tenant_id, contact_id, actor_id, payload)

    async def delete_contact(self, tenant_id: uuid.UUID, contact_id: uuid.UUID) -> None:
        await self._service.delete_contact(tenant_id, contact_id)
