import uuid

from app.modules.contacts.exceptions import ContactNotFound, InvalidCompanyReference
from app.modules.contacts.models import Contact
from app.modules.contacts.repository import ContactRepository
from app.modules.contacts.schemas import (
    ContactCreate,
    ContactListResponse,
    ContactResponse,
    ContactUpdate,
)
from app.shared.contracts.company_contract import CompanyContractProtocol


class ContactService:
    """Internal domain logic for contacts. Never imported from outside this module."""

    def __init__(
        self, repo: ContactRepository, companies: CompanyContractProtocol | None = None,
    ) -> None:
        self._repo = repo
        # Optional so existing tests/call sites that never touch company_id
        # don't need to wire a companies dependency they don't use.
        self._companies = companies

    async def _validate_company_id(self, tenant_id: uuid.UUID, company_id: uuid.UUID) -> None:
        if self._companies is None:
            return
        if not await self._companies.company_exists(tenant_id, company_id):
            raise InvalidCompanyReference()

    async def create_contact(
        self, tenant_id: uuid.UUID, actor_id: uuid.UUID, payload: ContactCreate
    ) -> ContactResponse:
        data = payload.model_dump(exclude_unset=True)
        data["tenant_id"] = tenant_id
        data["created_by"] = actor_id
        if data.get("company_id") is not None:
            data["company_id"] = uuid.UUID(data["company_id"])
            await self._validate_company_id(tenant_id, data["company_id"])
        if data.get("owner_id") is not None:
            data["owner_id"] = uuid.UUID(data["owner_id"])
        contact = await self._repo.create(data)
        return self._to_response(contact)

    async def get_contact(
        self, tenant_id: uuid.UUID, contact_id: uuid.UUID
    ) -> ContactResponse:
        contact = await self._repo.get_by_id(tenant_id, contact_id)
        if contact is None:
            raise ContactNotFound()
        return self._to_response(contact)

    async def list_contacts(
        self, tenant_id: uuid.UUID, page: int, page_size: int
    ) -> ContactListResponse:
        offset = (page - 1) * page_size
        items, total = await self._repo.list(tenant_id, page_size, offset)
        return ContactListResponse(
            items=[self._to_response(c) for c in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def update_contact(
        self,
        tenant_id: uuid.UUID,
        contact_id: uuid.UUID,
        actor_id: uuid.UUID,
        payload: ContactUpdate,
    ) -> ContactResponse:
        contact = await self._repo.get_by_id(tenant_id, contact_id)
        if contact is None:
            raise ContactNotFound()
        data = payload.model_dump(exclude_unset=True)
        if data.get("company_id") is not None:
            data["company_id"] = uuid.UUID(data["company_id"])
            await self._validate_company_id(tenant_id, data["company_id"])
        if data.get("owner_id") is not None:
            data["owner_id"] = uuid.UUID(data["owner_id"])
        data["updated_by"] = actor_id
        contact = await self._repo.update(contact, data)
        return self._to_response(contact)

    async def delete_contact(self, tenant_id: uuid.UUID, contact_id: uuid.UUID) -> None:
        contact = await self._repo.get_by_id(tenant_id, contact_id)
        if contact is None:
            raise ContactNotFound()
        await self._repo.delete(contact)

    @staticmethod
    def _to_response(contact: Contact) -> ContactResponse:
        return ContactResponse(
            id=str(contact.id),
            tenant_id=str(contact.tenant_id),
            owner_id=str(contact.owner_id) if contact.owner_id else None,
            company_id=str(contact.company_id) if contact.company_id else None,
            first_name=contact.first_name,
            last_name=contact.last_name,
            email=contact.email,
            secondary_email=contact.secondary_email,
            phone=contact.phone,
            mobile_phone=contact.mobile_phone,
            job_title=contact.job_title,
            department=contact.department,
            status=contact.status,
            lifecycle_stage=contact.lifecycle_stage,
            lead_source=contact.lead_source,
            linkedin_url=contact.linkedin_url,
            twitter_handle=contact.twitter_handle,
            address_line1=contact.address_line1,
            city=contact.city,
            state=contact.state,
            postal_code=contact.postal_code,
            country=contact.country,
            timezone=contact.timezone,
            preferred_contact_method=contact.preferred_contact_method,
            preferred_language=contact.preferred_language,
            do_not_contact=contact.do_not_contact,
            description=contact.description,
            tags=contact.tags,
            custom_fields=contact.custom_fields,
            created_at=contact.created_at.isoformat(),
            updated_at=contact.updated_at.isoformat(),
        )
