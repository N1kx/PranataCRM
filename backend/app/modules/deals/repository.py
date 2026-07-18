# Postponed evaluation of annotations: this class defines a method named
# `list`, which shadows the builtin `list` inside the class body for any
# annotation written after it under Python's default eager annotation
# evaluation. Deferring annotation evaluation avoids that entirely.
from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.sql import ColumnElement

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.deals.models import Deal
from app.modules.deals.schemas import ALLOWED_SORT_FIELDS


class DealRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: dict) -> Deal:
        deal = Deal(**data)
        self._session.add(deal)
        await self._session.flush()
        return deal

    async def get_by_id(self, tenant_id: uuid.UUID, deal_id: uuid.UUID) -> Deal | None:
        result = await self._session.execute(
            select(Deal).where(Deal.tenant_id == tenant_id, Deal.id == deal_id)
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        tenant_id: uuid.UUID,
        limit: int,
        offset: int,
        *,
        stage: str | None = None,
        status: str | None = None,
        deal_type: str | None = None,
        priority: str | None = None,
        owner_id: uuid.UUID | None = None,
        contact_id: uuid.UUID | None = None,
        company_id: uuid.UUID | None = None,
        q: str | None = None,
        sort: str = "created_at",
        order: str = "desc",
    ) -> tuple[list[Deal], int]:
        filters: list[ColumnElement] = [Deal.tenant_id == tenant_id]
        if stage is not None:
            filters.append(Deal.stage == stage)
        if status is not None:
            filters.append(Deal.status == status)
        if deal_type is not None:
            filters.append(Deal.deal_type == deal_type)
        if priority is not None:
            filters.append(Deal.priority == priority)
        if owner_id is not None:
            filters.append(Deal.owner_id == owner_id)
        if contact_id is not None:
            filters.append(Deal.contact_id == contact_id)
        if company_id is not None:
            filters.append(Deal.company_id == company_id)
        if q:
            # Escape LIKE wildcards so a term containing % or _ matches those
            # characters literally instead of acting as a pattern.
            escaped = q.lower().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            filters.append(func.lower(Deal.title).like(f"%{escaped}%", escape="\\"))

        # sort is validated against ALLOWED_SORT_FIELDS by the router before
        # reaching here, so this lookup never raises for a request that made
        # it this far — but fail closed rather than silently sorting by an
        # unintended column if that invariant is ever broken upstream.
        sort_column = getattr(Deal, ALLOWED_SORT_FIELDS.get(sort, "created_at"))
        order_by = sort_column.desc() if order == "desc" else sort_column.asc()

        items_result = await self._session.execute(
            select(Deal)
            .where(*filters)
            # id is a UUID v7 (time-ordered) tie-break so pagination never
            # skips/duplicates rows that share the same sort-column value.
            .order_by(order_by, Deal.id.desc())
            .limit(limit)
            .offset(offset)
        )
        total_result = await self._session.execute(
            select(func.count()).select_from(Deal).where(*filters)
        )
        return list(items_result.scalars().all()), total_result.scalar_one()

    async def update(self, deal: Deal, data: dict) -> Deal:
        for key, value in data.items():
            setattr(deal, key, value)
        await self._session.flush()
        # updated_at (onupdate=func.now()) is expired by the flush; refresh it
        # here — while still inside an async/greenlet context — so callers can
        # safely read it afterwards without triggering a lazy-load.
        await self._session.refresh(deal)
        return deal

    async def delete(self, deal: Deal) -> None:
        # TODO(ADR-005): publish a deal-deleted event once EventBus exists so
        # activities.deal_id references can be cleaned up. Until then, and
        # until the Activities module exists, orphaned activities.deal_id
        # rows are an accepted gap.
        await self._session.delete(deal)
        await self._session.flush()
