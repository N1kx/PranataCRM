from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import engine
from app.shared.exceptions import register_exception_handlers
from app.shared.logging import configure_logging
from app.shared.middleware import RequestIDMiddleware

configure_logging()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ───────────────────────────────────────────────────────────────
    app.state.redis = aioredis.from_url(
        settings.redis_url, decode_responses=True, socket_connect_timeout=5
    )
    await app.state.redis.ping()

    yield

    # ── Shutdown ──────────────────────────────────────────────────────────────
    await app.state.redis.aclose()
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    # Starlette's own debug mode renders a raw traceback response for unhandled
    # exceptions and bypasses our Exception handler entirely, which breaks both
    # the structured JSON logging and the { "error": {...} } envelope. Keep it
    # off regardless of app_debug (which still controls SQL echo logging).
    debug=False,
    lifespan=lifespan,
)

register_exception_handlers(app)

app.add_middleware(RequestIDMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"] if not settings.is_production else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # Let browser JS read the request id so the frontend can surface it in
    # error messages for support/correlation.
    expose_headers=["X-Request-ID"],
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

from app.modules.auth.router import router as auth_router, users_router
from app.modules.contacts.router import router as contacts_router
from app.modules.companies.router import router as companies_router
from app.modules.deals.router import router as deals_router
from app.modules.ai.router import router as ai_router
from app.modules.billing.router import router as billing_router
from app.modules.geo.router import router as geo_router
from app.modules.geo.admin_router import router as geo_admin_router

API_PREFIX = "/api/v1"

app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(users_router, prefix=API_PREFIX)
app.include_router(contacts_router, prefix=API_PREFIX)
app.include_router(companies_router, prefix=API_PREFIX)
app.include_router(deals_router, prefix=API_PREFIX)
app.include_router(ai_router, prefix=API_PREFIX)
app.include_router(billing_router, prefix=API_PREFIX)
app.include_router(geo_router, prefix=API_PREFIX)
app.include_router(geo_admin_router, prefix=API_PREFIX)
