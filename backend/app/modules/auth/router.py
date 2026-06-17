from fastapi import APIRouter

# Endpoints will be defined here once schemas.py (request/response shapes) is finalized.
# Each endpoint must call AuthUseCase only — no business logic in this file.
# Planned routes: POST /auth/register, POST /auth/login, POST /auth/refresh, POST /auth/logout

router = APIRouter(prefix="/auth", tags=["auth"])
