import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.container import get_auth_usecase
from app.database import get_db as get_session
from app.modules.auth.dependencies import CurrentUser, get_current_user
from app.modules.auth.exceptions import PermissionDenied
from app.modules.auth.schemas import (
    AcceptInviteRequest,
    AuthUserResponse,
    CreateUserRequest,
    InviteUserRequest,
    InviteSentResponse,
    LoginRequest,
    MeResponse,
    RegisterTenantRequest,
    RegisterTenantResponse,
    UserSummary,
)
from app.modules.auth.use_case import AuthUseCase
from app.shared.types import SuiteRole
from app.config import get_settings

router = APIRouter(prefix="/auth", tags=["auth"])
users_router = APIRouter(prefix="/users", tags=["users"])

# CurrentUser/get_current_user live in app.modules.auth.dependencies; they are
# imported above for this module's own endpoints and re-exported here so the
# existing tests that patch app.modules.auth.router.get_current_user keep working.
# get_auth_usecase is re-exported from app.container for the same reason —
# existing tests patch app.modules.auth.router.get_auth_usecase.
__all__ = ["router", "users_router", "CurrentUser", "get_current_user", "get_auth_usecase"]


def _get_tenant_slug(request: Request) -> str | None:
    settings = get_settings()
    if settings.app_env == "development":
        slug = request.headers.get("X-Tenant-Slug")
        if slug:
            return slug
    host = request.headers.get("host", "")
    parts = host.split(".")
    if len(parts) >= 3:
        return parts[0]
    return None


def _set_auth_cookies(response: Response, access: str, refresh: str) -> None:
    settings = get_settings()
    secure = settings.app_env != "development"
    response.set_cookie(
        "access_token", access, httponly=True, secure=secure,
        samesite="lax", max_age=settings.jwt_access_token_expire_minutes * 60, path="/"
    )
    response.set_cookie(
        "refresh_token", refresh, httponly=True, secure=secure,
        samesite="lax", max_age=settings.jwt_refresh_token_expire_days * 24 * 3600, path="/"
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/register-tenant", response_model=RegisterTenantResponse, status_code=201)
async def register_tenant(
    payload: RegisterTenantRequest,
    auth: Annotated[AuthUseCase, Depends(get_auth_usecase)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> RegisterTenantResponse:
    result = await auth.register_tenant(payload)
    await session.commit()
    return result


@router.post("/login", response_model=AuthUserResponse)
async def login(
    request: Request,
    payload: LoginRequest,
    response: Response,
    auth: Annotated[AuthUseCase, Depends(get_auth_usecase)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AuthUserResponse:
    tenant_slug = _get_tenant_slug(request) or ""
    from app.modules.auth.exceptions import TenantNotFound
    if not tenant_slug:
        raise TenantNotFound()

    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    user, access, refresh = await auth.login(payload, tenant_slug, ip, ua)
    await session.commit()
    _set_auth_cookies(response, access, refresh)
    return user


@router.post("/logout", status_code=200)
async def logout(
    request: Request,
    response: Response,
    auth: Annotated[AuthUseCase, Depends(get_auth_usecase)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    refresh_token = request.cookies.get("refresh_token")
    await auth.logout(refresh_token)
    await session.commit()
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    return {"message": "Signed out successfully."}


@router.get("/me", response_model=MeResponse)
async def me(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    auth: Annotated[AuthUseCase, Depends(get_auth_usecase)],
) -> MeResponse:
    return await auth.get_me(current_user.user_id)


@router.post("/accept-invite", response_model=AuthUserResponse, status_code=201)
async def accept_invite(
    payload: AcceptInviteRequest,
    auth: Annotated[AuthUseCase, Depends(get_auth_usecase)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AuthUserResponse:
    result = await auth.accept_invite(payload)
    await session.commit()
    return result


# ── User management (prefix: /users) ─────────────────────────────────────────

@users_router.post("", response_model=AuthUserResponse, status_code=201)
async def create_user(
    payload: CreateUserRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    auth: Annotated[AuthUseCase, Depends(get_auth_usecase)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AuthUserResponse:
    if current_user.suite_role not in (SuiteRole.TENANT_OWNER, SuiteRole.TENANT_ADMIN):
        raise PermissionDenied()
    result = await auth.create_user(
        payload, actor_id=current_user.user_id, tenant_id=current_user.tenant_id
    )
    await session.commit()
    return result


@users_router.get("/search", response_model=list[UserSummary])
async def search_users(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    auth: Annotated[AuthUseCase, Depends(get_auth_usecase)],
    q: str = "",
    # Bounded at the edge so a crafted value (e.g. -1 -> SQL "LIMIT -1", which
    # Postgres rejects) can't reach the query and 500 the endpoint.
    limit: int = Query(default=20, ge=1, le=50),
) -> list[UserSummary]:
    return await auth.search_users(current_user.tenant_id, q, limit)


@users_router.get("/lookup", response_model=list[UserSummary])
async def lookup_users(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    auth: Annotated[AuthUseCase, Depends(get_auth_usecase)],
    ids: str = "",
) -> list[UserSummary]:
    parsed = []
    for x in ids.split(","):
        x = x.strip()
        if not x:
            continue
        try:
            parsed.append(uuid.UUID(x))
        except ValueError:
            continue
    return await auth.lookup_users(current_user.tenant_id, parsed)


@users_router.post("/invite", response_model=InviteSentResponse, status_code=200)
async def invite_user(
    payload: InviteUserRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    auth: Annotated[AuthUseCase, Depends(get_auth_usecase)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> InviteSentResponse:
    if current_user.suite_role not in (SuiteRole.TENANT_OWNER, SuiteRole.TENANT_ADMIN):
        raise PermissionDenied()
    await auth.invite_user(
        payload, actor_id=current_user.user_id, tenant_id=current_user.tenant_id
    )
    await session.commit()
    return InviteSentResponse()
