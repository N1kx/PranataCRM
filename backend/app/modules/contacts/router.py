import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.container import get_contact_usecase
from app.database import get_db as get_session
from app.modules.contacts.exceptions import ContactQueryValidationError
from app.modules.contacts.schemas import (
    ALLOWED_SORT_FIELDS,
    ContactCreate,
    ContactListResponse,
    ContactResponse,
    ContactUpdate,
)
from app.modules.contacts.use_case import ContactUseCase
from app.shared.contracts.auth_contract import CurrentUser, get_current_user
from app.shared.types import ContactStatus, LifecycleStage

router = APIRouter(prefix="/contacts", tags=["contacts"])

_MAX_PAGE_SIZE = 100
_ALLOWED_STATUS = {s.value for s in ContactStatus}
_ALLOWED_LIFECYCLE_STAGE = {s.value for s in LifecycleStage}


@router.post("", response_model=ContactResponse, status_code=201)
async def create_contact(
    payload: ContactCreate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    contacts: Annotated[ContactUseCase, Depends(get_contact_usecase)],
) -> ContactResponse:
    result = await contacts.create_contact(
        current_user.tenant_id, current_user.user_id, payload
    )
    await session.commit()
    return result


@router.get("", response_model=ContactListResponse)
async def list_contacts(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    contacts: Annotated[ContactUseCase, Depends(get_contact_usecase)],
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    lifecycle_stage: str | None = None,
    owner_id: str | None = None,
    company_id: str | None = None,
    q: str | None = Query(default=None, max_length=100),
    sort: str = "created_at",
    order: str = "desc",
) -> ContactListResponse:
    page = max(page, 1)
    page_size = max(1, min(page_size, _MAX_PAGE_SIZE))

    # An empty/whitespace-only sort falls back to the default, same as an
    # omitted param — only a non-empty value outside the allowlist is a 422.
    sort = sort.strip() or "created_at"

    if status is not None and status not in _ALLOWED_STATUS:
        raise ContactQueryValidationError(
            f"status must be one of: {', '.join(sorted(_ALLOWED_STATUS))}."
        )
    if lifecycle_stage is not None and lifecycle_stage not in _ALLOWED_LIFECYCLE_STAGE:
        raise ContactQueryValidationError(
            f"lifecycle_stage must be one of: {', '.join(sorted(_ALLOWED_LIFECYCLE_STAGE))}."
        )
    if sort not in ALLOWED_SORT_FIELDS:
        raise ContactQueryValidationError(
            f"sort must be one of: {', '.join(sorted(ALLOWED_SORT_FIELDS))}."
        )
    if order not in ("asc", "desc"):
        raise ContactQueryValidationError("order must be one of: asc, desc.")

    owner_uuid: uuid.UUID | None = None
    if owner_id is not None:
        try:
            owner_uuid = uuid.UUID(owner_id)
        except ValueError:
            raise ContactQueryValidationError("owner_id must be a valid UUID.")

    company_uuid: uuid.UUID | None = None
    if company_id is not None:
        try:
            company_uuid = uuid.UUID(company_id)
        except ValueError:
            raise ContactQueryValidationError("company_id must be a valid UUID.")

    q = q.strip() or None if q is not None else None

    return await contacts.list_contacts(
        current_user.tenant_id,
        page,
        page_size,
        status=status,
        lifecycle_stage=lifecycle_stage,
        owner_id=owner_uuid,
        company_id=company_uuid,
        q=q,
        sort=sort,
        order=order,
    )


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: uuid.UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    contacts: Annotated[ContactUseCase, Depends(get_contact_usecase)],
) -> ContactResponse:
    return await contacts.get_contact(current_user.tenant_id, contact_id)


@router.patch("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: uuid.UUID,
    payload: ContactUpdate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    contacts: Annotated[ContactUseCase, Depends(get_contact_usecase)],
) -> ContactResponse:
    result = await contacts.update_contact(
        current_user.tenant_id, contact_id, current_user.user_id, payload
    )
    await session.commit()
    return result


@router.delete("/{contact_id}", status_code=200)
async def delete_contact(
    contact_id: uuid.UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    contacts: Annotated[ContactUseCase, Depends(get_contact_usecase)],
) -> dict:
    await contacts.delete_contact(current_user.tenant_id, contact_id)
    await session.commit()
    return {"message": "Contact deleted successfully."}
