from fastapi import APIRouter

# Endpoints will be defined here once schemas.py (request/response shapes) and
# deal_contract.py (DealDTO) are finalized.
# Each endpoint must call DealUseCase only — no business logic in this file.
# Planned routes: GET /deals, POST /deals, GET /deals/{id}, PATCH /deals/{id}/stage

router = APIRouter(prefix="/deals", tags=["deals"])
