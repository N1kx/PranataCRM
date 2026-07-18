import uuid

from app.modules.companies.exceptions import CompanyNotFound
from app.modules.companies.models import Company
from app.modules.companies.repository import CompanyRepository
from app.modules.companies.schemas import (
    CompanyCreate,
    CompanyListResponse,
    CompanyResponse,
    CompanySummary,
    CompanyUpdate,
)


class CompanyService:
    """Internal domain logic for companies. Never imported from outside this module."""

    def __init__(self, repo: CompanyRepository) -> None:
        self._repo = repo

    async def create_company(
        self, tenant_id: uuid.UUID, actor_id: uuid.UUID, payload: CompanyCreate
    ) -> CompanyResponse:
        data = payload.model_dump(exclude_unset=True)
        data["tenant_id"] = tenant_id
        data["created_by"] = actor_id
        if data.get("owner_id") is not None:
            data["owner_id"] = uuid.UUID(data["owner_id"])
        company = await self._repo.create(data)
        return self._to_response(company)

    async def get_company(
        self, tenant_id: uuid.UUID, company_id: uuid.UUID
    ) -> CompanyResponse:
        company = await self._repo.get_by_id(tenant_id, company_id)
        if company is None:
            raise CompanyNotFound()
        return self._to_response(company)

    async def company_exists(self, tenant_id: uuid.UUID, company_id: uuid.UUID) -> bool:
        return await self._repo.get_by_id(tenant_id, company_id) is not None

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
        offset = (page - 1) * page_size
        items, total = await self._repo.list(
            tenant_id,
            page_size,
            offset,
            status=status,
            company_type=company_type,
            size=size,
            industry=industry,
            owner_id=owner_id,
            q=q,
            sort=sort,
            order=order,
        )
        return CompanyListResponse(
            items=[self._to_response(c) for c in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def update_company(
        self,
        tenant_id: uuid.UUID,
        company_id: uuid.UUID,
        actor_id: uuid.UUID,
        payload: CompanyUpdate,
    ) -> CompanyResponse:
        company = await self._repo.get_by_id(tenant_id, company_id)
        if company is None:
            raise CompanyNotFound()
        data = payload.model_dump(exclude_unset=True)
        if data.get("owner_id") is not None:
            data["owner_id"] = uuid.UUID(data["owner_id"])
        data["updated_by"] = actor_id
        company = await self._repo.update(company, data)
        return self._to_response(company)

    async def delete_company(self, tenant_id: uuid.UUID, company_id: uuid.UUID) -> None:
        company = await self._repo.get_by_id(tenant_id, company_id)
        if company is None:
            raise CompanyNotFound()
        await self._repo.delete(company)

    async def search_companies(
        self, tenant_id: uuid.UUID, query: str, limit: int = 20
    ) -> list[CompanySummary]:
        rows = await self._repo.search(tenant_id, query, min(limit, 50))
        return [self._to_summary(c) for c in rows]

    async def lookup_companies(
        self, tenant_id: uuid.UUID, ids: list[uuid.UUID]
    ) -> list[CompanySummary]:
        rows = await self._repo.get_by_ids(tenant_id, ids[:100])
        return [self._to_summary(c) for c in rows]

    @staticmethod
    def _to_summary(company: Company) -> CompanySummary:
        return CompanySummary(id=str(company.id), name=company.name, domain=company.domain)

    @staticmethod
    def _to_response(company: Company) -> CompanyResponse:
        return CompanyResponse(
            id=str(company.id),
            tenant_id=str(company.tenant_id),
            owner_id=str(company.owner_id) if company.owner_id else None,
            name=company.name,
            legal_name=company.legal_name,
            domain=company.domain,
            website=company.website,
            email=company.email,
            phone=company.phone,
            industry=company.industry,
            size=company.size,
            employee_count=company.employee_count,
            company_type=company.company_type,
            status=company.status,
            arr=company.arr,
            annual_revenue=company.annual_revenue,
            source=company.source,
            source_other=company.source_other,
            address_line1=company.address_line1,
            address_line2=company.address_line2,
            city=company.city,
            state=company.state,
            postal_code=company.postal_code,
            country=company.country,
            timezone=company.timezone,
            linkedin_url=company.linkedin_url,
            twitter_handle=company.twitter_handle,
            logo_url=company.logo_url,
            description=company.description,
            tags=company.tags,
            custom_fields=company.custom_fields,
            created_at=company.created_at.isoformat(),
            updated_at=company.updated_at.isoformat(),
        )
