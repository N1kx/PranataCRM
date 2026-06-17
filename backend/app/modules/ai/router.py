from fastapi import APIRouter

# Endpoints will be defined here once ai_contract.py (DTOs) is finalized.
# Each endpoint must call AIUseCase only — no business logic in this file.
# Planned routes: POST /ai/chat, POST /ai/summarize, POST /ai/deals/{id}/score

router = APIRouter(prefix="/ai", tags=["ai"])
