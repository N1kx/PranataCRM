from fastapi import APIRouter

# Endpoints will be defined here once schemas.py (request/response shapes) and
# contact_contract.py (ContactDTO) are finalized.
# Each endpoint must call ContactUseCase only — no business logic in this file.
# Planned routes: GET /contacts, POST /contacts, GET /contacts/{id}, DELETE /contacts/{id}

router = APIRouter(prefix="/contacts", tags=["contacts"])
