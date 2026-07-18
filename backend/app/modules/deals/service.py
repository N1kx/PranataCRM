import uuid
from datetime import date, datetime, timezone
from decimal import ROUND_HALF_UP, Decimal

from app.modules.deals.exceptions import DealNotFound, InvalidStageTransition
from app.modules.deals.models import Deal
from app.modules.deals.repository import DealRepository
from app.modules.deals.schemas import (
    DealCreate,
    DealListResponse,
    DealResponse,
    DealStageUpdate,
    DealUpdate,
)
from app.shared.types import DealStage, DealStatus

# The only status values the generic PATCH /deals/{id} endpoint may ever
# write. 'won'/'lost' are set exclusively by the stage endpoint's side
# effects (see update_stage).
_PATCHABLE_STATUSES = {DealStatus.OPEN.value, DealStatus.ABANDONED.value}

_OPEN_STAGES = {DealStage.LEAD.value, DealStage.QUALIFIED.value, DealStage.PROPOSAL.value}


def _compute_weighted_value(value: Decimal, probability: int) -> Decimal:
    return (value * Decimal(probability) / Decimal(100)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )


class DealService:
    """Internal domain logic for deals. Never imported from outside this module.
    Knows nothing about other modules — contact_id/company_id/owner_id existence
    is validated one layer up, in DealUseCase, via the respective contracts."""

    def __init__(self, repo: DealRepository) -> None:
        self._repo = repo

    async def create_deal(
        self, tenant_id: uuid.UUID, actor_id: uuid.UUID, payload: DealCreate
    ) -> DealResponse:
        data = payload.model_dump(exclude_unset=True)
        for key in ("contact_id", "company_id", "owner_id"):
            if data.get(key) is not None:
                data[key] = uuid.UUID(data[key])

        value = data.get("value", Decimal("0"))
        probability = data.get("probability", 0)
        data["value"] = value
        data["probability"] = probability
        data["currency"] = data.get("currency") or "IDR"
        data["stage"] = data.get("stage") or DealStage.LEAD.value
        # status is always server-derived on create — never accepted from the
        # client (DealCreate has no status field at all).
        data["status"] = DealStatus.OPEN.value
        data["weighted_value"] = _compute_weighted_value(value, probability)
        data["stage_changed_at"] = datetime.now(timezone.utc)

        data["tenant_id"] = tenant_id
        data["created_by"] = actor_id
        deal = await self._repo.create(data)
        return self._to_response(deal)

    async def get_deal(self, tenant_id: uuid.UUID, deal_id: uuid.UUID) -> DealResponse:
        deal = await self._repo.get_by_id(tenant_id, deal_id)
        if deal is None:
            raise DealNotFound()
        return self._to_response(deal)

    async def deal_exists(self, tenant_id: uuid.UUID, deal_id: uuid.UUID) -> bool:
        return await self._repo.get_by_id(tenant_id, deal_id) is not None

    async def list_deals(
        self,
        tenant_id: uuid.UUID,
        page: int,
        page_size: int,
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
    ) -> DealListResponse:
        offset = (page - 1) * page_size
        items, total = await self._repo.list(
            tenant_id,
            page_size,
            offset,
            stage=stage,
            status=status,
            deal_type=deal_type,
            priority=priority,
            owner_id=owner_id,
            contact_id=contact_id,
            company_id=company_id,
            q=q,
            sort=sort,
            order=order,
        )
        return DealListResponse(
            items=[self._to_response(d) for d in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def update_deal(
        self,
        tenant_id: uuid.UUID,
        deal_id: uuid.UUID,
        actor_id: uuid.UUID,
        payload: DealUpdate,
    ) -> DealResponse:
        deal = await self._repo.get_by_id(tenant_id, deal_id)
        if deal is None:
            raise DealNotFound()

        if "stage" in payload.model_fields_set:
            raise InvalidStageTransition(
                "stage cannot be changed via PATCH /deals/{id}; "
                "use PATCH /deals/{id}/stage instead."
            )

        data = payload.model_dump(exclude_unset=True)
        data.pop("stage", None)

        if "status" in payload.model_fields_set:
            new_status = data["status"]
            if new_status not in _PATCHABLE_STATUSES or deal.status not in _PATCHABLE_STATUSES:
                raise InvalidStageTransition(
                    "status may only be changed between 'open' and 'abandoned' here; "
                    "'won'/'lost' are set via PATCH /deals/{id}/stage."
                )

        for key in ("contact_id", "company_id", "owner_id"):
            if key in data and data[key] is not None:
                data[key] = uuid.UUID(data[key])

        if "value" in data or "probability" in data:
            new_value = data.get("value", deal.value)
            new_probability = data.get("probability", deal.probability)
            data["weighted_value"] = _compute_weighted_value(new_value, new_probability)

        data["updated_by"] = actor_id
        deal = await self._repo.update(deal, data)
        return self._to_response(deal)

    async def update_stage(
        self,
        tenant_id: uuid.UUID,
        deal_id: uuid.UUID,
        actor_id: uuid.UUID,
        payload: DealStageUpdate,
    ) -> DealResponse:
        deal = await self._repo.get_by_id(tenant_id, deal_id)
        if deal is None:
            raise DealNotFound()

        if deal.status == DealStatus.ABANDONED.value:
            raise InvalidStageTransition(
                "cannot change the stage of an abandoned deal; reopen it first."
            )

        if payload.stage == deal.stage:
            # Same-stage no-op: return the deal unchanged, no side effects,
            # no stage_changed_at bump.
            return self._to_response(deal)

        data: dict = {
            "stage": payload.stage,
            "stage_changed_at": datetime.now(timezone.utc),
        }

        today = date.today()
        if payload.stage == DealStage.WON.value:
            data["status"] = DealStatus.WON.value
            data["actual_close_date"] = deal.actual_close_date or today
            data["probability"] = 100
        elif payload.stage == DealStage.LOST.value:
            if not payload.lost_reason:
                raise InvalidStageTransition(
                    "lost_reason is required when stage is 'lost'."
                )
            data["status"] = DealStatus.LOST.value
            data["actual_close_date"] = deal.actual_close_date or today
            data["probability"] = 0
            data["lost_reason"] = payload.lost_reason
        elif payload.stage in _OPEN_STAGES:
            data["status"] = DealStatus.OPEN.value
            data["actual_close_date"] = None

        if payload.close_reason is not None:
            data["close_reason"] = payload.close_reason

        new_probability = data.get("probability", deal.probability)
        data["weighted_value"] = _compute_weighted_value(deal.value, new_probability)
        data["updated_by"] = actor_id

        deal = await self._repo.update(deal, data)
        return self._to_response(deal)

    async def delete_deal(self, tenant_id: uuid.UUID, deal_id: uuid.UUID) -> None:
        deal = await self._repo.get_by_id(tenant_id, deal_id)
        if deal is None:
            raise DealNotFound()
        await self._repo.delete(deal)

    @staticmethod
    def _to_response(deal: Deal) -> DealResponse:
        return DealResponse(
            id=str(deal.id),
            tenant_id=str(deal.tenant_id),
            contact_id=str(deal.contact_id) if deal.contact_id else None,
            company_id=str(deal.company_id) if deal.company_id else None,
            owner_id=str(deal.owner_id) if deal.owner_id else None,
            title=deal.title,
            description=deal.description,
            stage=deal.stage,
            status=deal.status,
            deal_type=deal.deal_type,
            value=deal.value,
            currency=deal.currency,
            probability=deal.probability,
            weighted_value=deal.weighted_value,
            expected_close_date=deal.expected_close_date,
            actual_close_date=deal.actual_close_date,
            stage_changed_at=deal.stage_changed_at.isoformat() if deal.stage_changed_at else None,
            priority=deal.priority,
            source=deal.source,
            next_step=deal.next_step,
            next_step_date=deal.next_step_date,
            competitor=deal.competitor,
            close_reason=deal.close_reason,
            lost_reason=deal.lost_reason,
            tags=deal.tags,
            custom_fields=deal.custom_fields,
            created_at=deal.created_at.isoformat(),
            updated_at=deal.updated_at.isoformat(),
        )
