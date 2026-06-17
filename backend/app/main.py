from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import engine
from app.shared.exceptions import AppError

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ───────────────────────────────────────────────────────────────
    app.state.redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    await app.state.redis.ping()

    yield

    # ── Shutdown ──────────────────────────────────────────────────────────────
    await app.state.redis.aclose()
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    debug=settings.app_debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"] if not settings.is_production else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Global error handler ──────────────────────────────────────────────────────

@app.exception_handler(AppError)
async def app_error_handler(request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health", tags=["health"])
async def health() -> dict:
    redis_ok = False
    db_ok = False

    try:
        await app.state.redis.ping()
        redis_ok = True
    except Exception:
        pass

    try:
        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    return {
        "status": "ok" if (redis_ok and db_ok) else "degraded",
        "redis": redis_ok,
        "db": db_ok,
    }


# ── Module routers ────────────────────────────────────────────────────────────

from app.modules.auth.router import router as auth_router
from app.modules.contacts.router import router as contacts_router
from app.modules.deals.router import router as deals_router
from app.modules.ai.router import router as ai_router
from app.modules.billing.router import router as billing_router

API_PREFIX = "/api/v1"

app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(contacts_router, prefix=API_PREFIX)
app.include_router(deals_router, prefix=API_PREFIX)
app.include_router(ai_router, prefix=API_PREFIX)
app.include_router(billing_router, prefix=API_PREFIX)
