# Postponed evaluation of annotations: this class defines a method named
# `list`, which shadows the builtin `list` inside the class body for any
# annotation written after it under Python's default eager annotation
# evaluation. Deferring annotation evaluation avoids that entirely.
from __future__ import annotations

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.sql import ColumnElement

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.contacts.models import Contact
from app.modules.contacts.schemas import ALLOWED_SORT_FIELDS


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
        self,
        tenant_id: uuid.UUID,
        limit: int,
        offset: int,
        *,
        status: str | None = None,
        lifecycle_stage: str | None = None,
        owner_id: uuid.UUID | None = None,
        company_id: uuid.UUID | None = None,
        q: str | None = None,
        sort: str = "created_at",
        order: str = "desc",
    ) -> tuple[list[Contact], int]:
        filters: list[ColumnElement] = [Contact.tenant_id == tenant_id]
        if status is not None:
            filters.append(Contact.status == status)
        if lifecycle_stage is not None:
            filters.append(Contact.lifecycle_stage == lifecycle_stage)
        if owner_id is not None:
            filters.append(Contact.owner_id == owner_id)
        if company_id is not None:
            filters.append(Contact.company_id == company_id)
        if q:
            # Escape LIKE wildcards so a term containing % or _ matches those
            # characters literally instead of acting as a pattern.
            escaped = q.lower().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            pattern = f"%{escaped}%"
            filters.append(
                or_(
                    func.lower(Contact.first_name).like(pattern, escape="\\"),
                    func.lower(Contact.last_name).like(pattern, escape="\\"),
                    func.lower(Contact.email).like(pattern, escape="\\"),
                )
            )

        # sort is validated against ALLOWED_SORT_FIELDS by the router before
        # reaching here, so this lookup never raises for a request that made
        # it this far — but fail closed rather than silently sorting by an
        # unintended column if that invariant is ever broken upstream.
        sort_column = getattr(Contact, ALLOWED_SORT_FIELDS.get(sort, "created_at"))
        order_by = sort_column.desc() if order == "desc" else sort_column.asc()

        items_result = await self._session.execute(
            select(Contact)
            .where(*filters)
            # id is a UUID v7 (time-ordered) tie-break so pagination never
            # skips/duplicates rows that share the same sort-column value.
            .order_by(order_by, Contact.id.desc())
            .limit(limit)
            .offset(offset)
        )
        total_result = await self._session.execute(
            select(func.count()).select_from(Contact).where(*filters)
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
