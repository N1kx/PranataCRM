from fastapi import APIRouter

# Endpoints will be defined here once schemas.py (request/response shapes) and
# billing_contract.py (BillingStatusDTO) are finalized.
# Each endpoint must call BillingUseCase only — no business logic in this file.
# Planned routes: GET /billing/status/{tenant_id}, POST /billing/upgrade/{tenant_id}

router = APIRouter(prefix="/billing", tags=["billing"])
