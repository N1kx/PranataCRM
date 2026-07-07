import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db as get_session
from app.modules.contacts.repository import ContactRepository
from app.modules.contacts.schemas import (
    ContactCreate,
    ContactListResponse,
    ContactResponse,
    ContactUpdate,
)
from app.modules.contacts.service import ContactService
from app.shared.auth_dependency import CurrentUser, get_current_user

router = APIRouter(prefix="/contacts", tags=["contacts"])

_MAX_PAGE_SIZE = 100


@router.post("", response_model=ContactResponse, status_code=201)
async def create_contact(
    payload: ContactCreate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ContactResponse:
    service = ContactService(ContactRepository(session))
    result = await service.create_contact(
        current_user.tenant_id, current_user.user_id, payload
    )
    await session.commit()
    return result


@router.get("", response_model=ContactListResponse)
async def list_contacts(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    page: int = 1,
    page_size: int = 20,
) -> ContactListResponse:
    page = max(page, 1)
    page_size = max(1, min(page_size, _MAX_PAGE_SIZE))
    service = ContactService(ContactRepository(session))
    return await service.list_contacts(current_user.tenant_id, page, page_size)


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: uuid.UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ContactResponse:
    service = ContactService(ContactRepository(session))
    return await service.get_contact(current_user.tenant_id, contact_id)


@router.patch("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: uuid.UUID,
    payload: ContactUpdate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ContactResponse:
    service = ContactService(ContactRepository(session))
    result = await service.update_contact(
        current_user.tenant_id, contact_id, current_user.user_id, payload
    )
    await session.commit()
    return result


@router.delete("/{contact_id}", status_code=200)
async def delete_contact(
    contact_id: uuid.UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = ContactService(ContactRepository(session))
    await service.delete_contact(current_user.tenant_id, contact_id)
    await session.commit()
    return {"message": "Contact deleted successfully."}
