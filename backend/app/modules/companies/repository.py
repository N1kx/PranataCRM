# Postponed evaluation of annotations: this class defines a method named
# `list`, which shadows the builtin `list` inside the class body for any
# annotation written after it (e.g. `-> list[Company]` on a later method
# would resolve `list` to the method itself, not the builtin, and crash at
# import time). Deferring annotation evaluation avoids that entirely.
from __future__ import annotations

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.sql import ColumnElement

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.companies.models import Company
from app.modules.companies.schemas import ALLOWED_SORT_FIELDS


class CompanyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: dict) -> Company:
        company = Company(**data)
        self._session.add(company)
        await self._session.flush()
        return company

    async def get_by_id(self, tenant_id: uuid.UUID, company_id: uuid.UUID) -> Company | None:
        result = await self._session.execute(
            select(Company).where(
                Company.tenant_id == tenant_id, Company.id == company_id
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
        company_type: str | None = None,
        size: str | None = None,
        industry: str | None = None,
        owner_id: uuid.UUID | None = None,
        q: str | None = None,
        sort: str = "created_at",
        order: str = "desc",
    ) -> tuple[list[Company], int]:
        filters: list[ColumnElement] = [Company.tenant_id == tenant_id]
        if status is not None:
            filters.append(Company.status == status)
        if company_type is not None:
            filters.append(Company.company_type == company_type)
        if size is not None:
            filters.append(Company.size == size)
        if industry is not None:
            filters.append(func.lower(Company.industry) == industry.lower())
        if owner_id is not None:
            filters.append(Company.owner_id == owner_id)
        if q:
            # Escape LIKE wildcards so a term containing % or _ matches those
            # characters literally instead of acting as a pattern.
            escaped = q.lower().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            pattern = f"%{escaped}%"
            filters.append(
                or_(
                    func.lower(Company.name).like(pattern, escape="\\"),
                    func.lower(Company.legal_name).like(pattern, escape="\\"),
                    func.lower(Company.domain).like(pattern, escape="\\"),
                    func.lower(Company.email).like(pattern, escape="\\"),
                )
            )

        # sort is validated against ALLOWED_SORT_FIELDS by the router/schema
        # layer before reaching here, so this lookup never raises for a request
        # that made it this far — but fail closed rather than silently sorting
        # by an unintended column if that invariant is ever broken upstream.
        sort_column = getattr(Company, ALLOWED_SORT_FIELDS.get(sort, "created_at"))
        order_by = sort_column.desc() if order == "desc" else sort_column.asc()

        items_result = await self._session.execute(
            select(Company)
            .where(*filters)
            # id is a UUID v7 (time-ordered) tie-break so pagination never
            # skips/duplicates rows that share the same sort-column value.
            .order_by(order_by, Company.id.desc())
            .limit(limit)
            .offset(offset)
        )
        total_result = await self._session.execute(
            select(func.count()).select_from(Company).where(*filters)
        )
        return list(items_result.scalars().all()), total_result.scalar_one()

    async def search(
        self, tenant_id: uuid.UUID, query: str, limit: int = 20
    ) -> list[Company]:
        stmt = select(Company).where(
            Company.tenant_id == tenant_id,
            Company.status == "active",
        )
        q = (query or "").strip()
        if q:
            # Escape LIKE wildcards so a term such as "50%" or "a_b" matches
            # those characters literally instead of acting as a pattern.
            escaped = q.lower().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            like = f"%{escaped}%"
            stmt = stmt.where(
                func.lower(Company.name).like(like, escape="\\")
                | func.lower(Company.domain).like(like, escape="\\")
            )
        stmt = stmt.order_by(Company.name).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_ids(
        self, tenant_id: uuid.UUID, ids: list[uuid.UUID]
    ) -> list[Company]:
        if not ids:
            return []
        result = await self._session.execute(
            select(Company).where(Company.tenant_id == tenant_id, Company.id.in_(ids))
        )
        return list(result.scalars().all())

    async def update(self, company: Company, data: dict) -> Company:
        for key, value in data.items():
            setattr(company, key, value)
        await self._session.flush()
        # updated_at (onupdate=func.now()) is expired by the flush; refresh it
        # here — while still inside an async/greenlet context — so callers can
        # safely read it afterwards without triggering a lazy-load.
        await self._session.refresh(company)
        return company

    async def delete(self, company: Company) -> None:
        await self._session.delete(company)
        await self._session.flush()
