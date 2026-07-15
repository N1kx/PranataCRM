import uuid

from app.modules.contacts.exceptions import InvalidCompanyReference
from app.modules.contacts.schemas import (
    ContactCreate,
    ContactListResponse,
    ContactResponse,
    ContactUpdate,
)
from app.modules.contacts.service import ContactService
from app.shared.contracts.company_contract import CompanyContractProtocol


class ContactUseCase:
    """Entry point for the contacts module — its router calls in through here,
    never through ContactService directly. No other module currently consumes
    contacts data, so there is no ContactContractProtocol yet (see
    shared/contracts/contact_contract.py); this will implement it once one is
    needed. Depends on CompanyContractProtocol (not the concrete companies
    module) to validate a company_id reference."""

    def __init__(self, service: ContactService, companies: CompanyContractProtocol) -> None:
        self._service = service
        self._companies = companies

    async def _validate_company_id(self, tenant_id: uuid.UUID, company_id: str | None) -> None:
        if company_id is None:
            return
        if not await self._companies.company_exists(tenant_id, uuid.UUID(company_id)):
            raise InvalidCompanyReference()

    async def create_contact(
        self, tenant_id: uuid.UUID, actor_id: uuid.UUID, payload: ContactCreate
    ) -> ContactResponse:
        await self._validate_company_id(tenant_id, payload.company_id)
        return await self._service.create_contact(tenant_id, actor_id, payload)

    async def get_contact(
        self, tenant_id: uuid.UUID, contact_id: uuid.UUID
    ) -> ContactResponse:
        return await self._service.get_contact(tenant_id, contact_id)

    async def list_contacts(
        self, tenant_id: uuid.UUID, page: int, page_size: int
    ) -> ContactListResponse:
        return await self._service.list_contacts(tenant_id, page, page_size)

    async def update_contact(
        self,
        tenant_id: uuid.UUID,
        contact_id: uuid.UUID,
        actor_id: uuid.UUID,
        payload: ContactUpdate,
    ) -> ContactResponse:
        # company_id is only present in model_fields_set when the client sent
        # it explicitly (not merely defaulted to None) — this is what lets a
        # partial PATCH omit company_id entirely without triggering validation,
        # while still validating an explicit non-null value or skipping an
        # explicit null (unassign), matching ContactUpdate's own semantics.
        if "company_id" in payload.model_fields_set:
            await self._validate_company_id(tenant_id, payload.company_id)
        return await self._service.update_contact(tenant_id, contact_id, actor_id, payload)

    async def delete_contact(self, tenant_id: uuid.UUID, contact_id: uuid.UUID) -> None:
        await self._service.delete_contact(tenant_id, contact_id)
