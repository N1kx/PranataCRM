import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.container import get_deal_usecase
from app.database import get_db as get_session
from app.modules.deals.exceptions import DealQueryValidationError
from app.modules.deals.schemas import (
    ALLOWED_SORT_FIELDS,
    DealCreate,
    DealListResponse,
    DealResponse,
    DealStageUpdate,
    DealUpdate,
)
from app.modules.deals.use_case import DealUseCase
from app.shared.contracts.auth_contract import CurrentUser, get_current_user
from app.shared.types import DealStatus, DealType, Priority
from app.shared.types import DealStage as DealStageEnum

router = APIRouter(prefix="/deals", tags=["deals"])

_MAX_PAGE_SIZE = 100
_ALLOWED_STAGE = {s.value for s in DealStageEnum}
_ALLOWED_STATUS = {s.value for s in DealStatus}
_ALLOWED_DEAL_TYPE = {t.value for t in DealType}
_ALLOWED_PRIORITY = {p.value for p in Priority}


@router.post("", response_model=DealResponse, status_code=201)
async def create_deal(
    payload: DealCreate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    deals: Annotated[DealUseCase, Depends(get_deal_usecase)],
) -> DealResponse:
    result = await deals.create_deal(current_user.tenant_id, current_user.user_id, payload)
    await session.commit()
    return result


@router.get("", response_model=DealListResponse)
async def list_deals(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    deals: Annotated[DealUseCase, Depends(get_deal_usecase)],
    page: int = 1,
    page_size: int = 20,
    stage: str | None = None,
    status: str | None = None,
    deal_type: str | None = None,
    priority: str | None = None,
    owner_id: str | None = None,
    contact_id: str | None = None,
    company_id: str | None = None,
    q: str | None = Query(default=None, max_length=100),
    sort: str = "created_at",
    order: str = "desc",
) -> DealListResponse:
    page = max(page, 1)
    page_size = max(1, min(page_size, _MAX_PAGE_SIZE))

    # An empty/whitespace-only sort falls back to the default, same as an
    # omitted param — only a non-empty value outside the allowlist is a 422.
    sort = sort.strip() or "created_at"

    if stage is not None and stage not in _ALLOWED_STAGE:
        raise DealQueryValidationError(
            f"stage must be one of: {', '.join(sorted(_ALLOWED_STAGE))}."
        )
    if status is not None and status not in _ALLOWED_STATUS:
        raise DealQueryValidationError(
            f"status must be one of: {', '.join(sorted(_ALLOWED_STATUS))}."
        )
    if deal_type is not None and deal_type not in _ALLOWED_DEAL_TYPE:
        raise DealQueryValidationError(
            f"deal_type must be one of: {', '.join(sorted(_ALLOWED_DEAL_TYPE))}."
        )
    if priority is not None and priority not in _ALLOWED_PRIORITY:
        raise DealQueryValidationError(
            f"priority must be one of: {', '.join(sorted(_ALLOWED_PRIORITY))}."
        )
    if sort not in ALLOWED_SORT_FIELDS:
        raise DealQueryValidationError(
            f"sort must be one of: {', '.join(sorted(ALLOWED_SORT_FIELDS))}."
        )
    if order not in ("asc", "desc"):
        raise DealQueryValidationError("order must be one of: asc, desc.")

    owner_uuid: uuid.UUID | None = None
    if owner_id is not None:
        try:
            owner_uuid = uuid.UUID(owner_id)
        except ValueError:
            raise DealQueryValidationError("owner_id must be a valid UUID.")

    contact_uuid: uuid.UUID | None = None
    if contact_id is not None:
        try:
            contact_uuid = uuid.UUID(contact_id)
        except ValueError:
            raise DealQueryValidationError("contact_id must be a valid UUID.")

    company_uuid: uuid.UUID | None = None
    if company_id is not None:
        try:
            company_uuid = uuid.UUID(company_id)
        except ValueError:
            raise DealQueryValidationError("company_id must be a valid UUID.")

    q = q.strip() or None if q is not None else None

    return await deals.list_deals(
        current_user.tenant_id,
        page,
        page_size,
        stage=stage,
        status=status,
        deal_type=deal_type,
        priority=priority,
        owner_id=owner_uuid,
        contact_id=contact_uuid,
        company_id=company_uuid,
        q=q,
        sort=sort,
        order=order,
    )


@router.get("/{deal_id}", response_model=DealResponse)
async def get_deal(
    deal_id: uuid.UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    deals: Annotated[DealUseCase, Depends(get_deal_usecase)],
) -> DealResponse:
    return await deals.get_deal(current_user.tenant_id, deal_id)


@router.patch("/{deal_id}", response_model=DealResponse)
async def update_deal(
    deal_id: uuid.UUID,
    payload: DealUpdate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    deals: Annotated[DealUseCase, Depends(get_deal_usecase)],
) -> DealResponse:
    result = await deals.update_deal(
        current_user.tenant_id, deal_id, current_user.user_id, payload
    )
    await session.commit()
    return result


@router.patch("/{deal_id}/stage", response_model=DealResponse)
async def update_deal_stage(
    deal_id: uuid.UUID,
    payload: DealStageUpdate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    deals: Annotated[DealUseCase, Depends(get_deal_usecase)],
) -> DealResponse:
    result = await deals.update_stage(
        current_user.tenant_id, deal_id, current_user.user_id, payload
    )
    await session.commit()
    return result


@router.delete("/{deal_id}", status_code=200)
async def delete_deal(
    deal_id: uuid.UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    deals: Annotated[DealUseCase, Depends(get_deal_usecase)],
) -> dict:
    await deals.delete_deal(current_user.tenant_id, deal_id)
    await session.commit()
    return {"message": "Deal deleted successfully."}
