import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.container import get_company_usecase
from app.database import get_db as get_session
from app.modules.companies.exceptions import CompanyQueryValidationError
from app.modules.companies.schemas import (
    ALLOWED_SORT_FIELDS,
    CompanyCreate,
    CompanyListResponse,
    CompanyResponse,
    CompanySummary,
    CompanyUpdate,
)
from app.modules.companies.use_case import CompanyUseCase
from app.shared.contracts.auth_contract import CurrentUser, get_current_user
from app.shared.types import CompanySize, CompanyType

router = APIRouter(prefix="/companies", tags=["companies"])

_MAX_PAGE_SIZE = 100
_ALLOWED_STATUS = {"active", "inactive"}
_ALLOWED_COMPANY_TYPE = {t.value for t in CompanyType}
_ALLOWED_SIZE = {s.value for s in CompanySize}


@router.post("", response_model=CompanyResponse, status_code=201)
async def create_company(
    payload: CompanyCreate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    companies: Annotated[CompanyUseCase, Depends(get_company_usecase)],
) -> CompanyResponse:
    result = await companies.create_company(
        current_user.tenant_id, current_user.user_id, payload
    )
    await session.commit()
    return result


@router.get("", response_model=CompanyListResponse)
async def list_companies(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    companies: Annotated[CompanyUseCase, Depends(get_company_usecase)],
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    company_type: str | None = None,
    size: str | None = None,
    industry: str | None = Query(default=None, max_length=100),
    owner_id: str | None = None,
    q: str | None = Query(default=None, max_length=100),
    sort: str = "created_at",
    order: str = "desc",
) -> CompanyListResponse:
    page = max(page, 1)
    page_size = max(1, min(page_size, _MAX_PAGE_SIZE))

    # An empty/whitespace-only sort falls back to the default, same as an
    # omitted param — only a non-empty value outside the allowlist is a 422.
    sort = sort.strip() or "created_at"

    if status is not None and status not in _ALLOWED_STATUS:
        raise CompanyQueryValidationError(
            f"status must be one of: {', '.join(sorted(_ALLOWED_STATUS))}."
        )
    if company_type is not None and company_type not in _ALLOWED_COMPANY_TYPE:
        raise CompanyQueryValidationError(
            f"company_type must be one of: {', '.join(sorted(_ALLOWED_COMPANY_TYPE))}."
        )
    if size is not None and size not in _ALLOWED_SIZE:
        raise CompanyQueryValidationError(
            f"size must be one of: {', '.join(sorted(_ALLOWED_SIZE))}."
        )
    if sort not in ALLOWED_SORT_FIELDS:
        raise CompanyQueryValidationError(
            f"sort must be one of: {', '.join(sorted(ALLOWED_SORT_FIELDS))}."
        )
    if order not in ("asc", "desc"):
        raise CompanyQueryValidationError("order must be one of: asc, desc.")

    owner_uuid: uuid.UUID | None = None
    if owner_id is not None:
        try:
            owner_uuid = uuid.UUID(owner_id)
        except ValueError:
            raise CompanyQueryValidationError("owner_id must be a valid UUID.")

    industry = industry.strip() or None if industry is not None else None
    q = q.strip() or None if q is not None else None

    return await companies.list_companies(
        current_user.tenant_id,
        page,
        page_size,
        status=status,
        company_type=company_type,
        size=size,
        industry=industry,
        owner_id=owner_uuid,
        q=q,
        sort=sort,
        order=order,
    )


@router.get("/search", response_model=list[CompanySummary])
async def search_companies(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    companies: Annotated[CompanyUseCase, Depends(get_company_usecase)],
    q: str = "",
    # Bounded at the edge so a crafted value (e.g. -1 -> SQL "LIMIT -1", which
    # Postgres rejects) can't reach the query and 500 the endpoint.
    limit: int = Query(default=20, ge=1, le=50),
) -> list[CompanySummary]:
    return await companies.search_companies(current_user.tenant_id, q, limit)


@router.get("/lookup", response_model=list[CompanySummary])
async def lookup_companies(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    companies: Annotated[CompanyUseCase, Depends(get_company_usecase)],
    ids: str = "",
) -> list[CompanySummary]:
    parsed = []
    for x in ids.split(","):
        x = x.strip()
        if not x:
            continue
        try:
            parsed.append(uuid.UUID(x))
        except ValueError:
            continue
    return await companies.lookup_companies(current_user.tenant_id, parsed)


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: uuid.UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    companies: Annotated[CompanyUseCase, Depends(get_company_usecase)],
) -> CompanyResponse:
    return await companies.get_company(current_user.tenant_id, company_id)


@router.patch("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: uuid.UUID,
    payload: CompanyUpdate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    companies: Annotated[CompanyUseCase, Depends(get_company_usecase)],
) -> CompanyResponse:
    result = await companies.update_company(
        current_user.tenant_id, company_id, current_user.user_id, payload
    )
    await session.commit()
    return result


@router.delete("/{company_id}", status_code=200)
async def delete_company(
    company_id: uuid.UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    companies: Annotated[CompanyUseCase, Depends(get_company_usecase)],
) -> dict:
    await companies.delete_company(current_user.tenant_id, company_id)
    await session.commit()
    return {"message": "Company deleted successfully."}
