import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.contacts.models import Contact


class ContactRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: dict) -> Contact:
        contact = Contact(**data)
        self._session.add(contact)
        await self._session.flush()
        return contact

    async def get_by_id(self, tenant_id: uuid.UUID, contact_id: uuid.UUID) -> Contact | None:
        result = await self._session.execute(
            select(Contact).where(
                Contact.tenant_id == tenant_id, Contact.id == contact_id
            )
        )
        return result.scalar_one_or_none()

    async def list(
        self, tenant_id: uuid.UUID, limit: int, offset: int
    ) -> tuple[list[Contact], int]:
        items_result = await self._session.execute(
            select(Contact)
            .where(Contact.tenant_id == tenant_id)
            .order_by(Contact.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        total_result = await self._session.execute(
            select(func.count()).select_from(Contact).where(Contact.tenant_id == tenant_id)
        )
        return list(items_result.scalars().all()), total_result.scalar_one()

    async def update(self, contact: Contact, data: dict) -> Contact:
        for key, value in data.items():
            setattr(contact, key, value)
        await self._session.flush()
        # updated_at (onupdate=func.now()) is expired by the flush; refresh it
        # here — while still inside an async/greenlet context — so callers can
        # safely read it afterwards without triggering a lazy-load.
        await self._session.refresh(contact)
        return contact

    async def delete(self, contact: Contact) -> None:
        await self._session.delete(contact)
        await self._session.flush()
