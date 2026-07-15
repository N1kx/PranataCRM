import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.container import get_contact_usecase
from app.database import get_db as get_session
from app.modules.contacts.schemas import (
    ContactCreate,
    ContactListResponse,
    ContactResponse,
    ContactUpdate,
)
from app.modules.contacts.use_case import ContactUseCase
from app.shared.contracts.auth_contract import CurrentUser, get_current_user

router = APIRouter(prefix="/contacts", tags=["contacts"])

_MAX_PAGE_SIZE = 100


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
) -> ContactListResponse:
    page = max(page, 1)
    page_size = max(1, min(page_size, _MAX_PAGE_SIZE))
    return await contacts.list_contacts(current_user.tenant_id, page, page_size)


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
