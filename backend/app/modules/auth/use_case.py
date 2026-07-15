import uuid

from app.modules.auth.schemas import (
    AcceptInviteRequest,
    AuthUserResponse,
    CreateUserRequest,
    InviteUserRequest,
    LoginRequest,
    MeResponse,
    RegisterTenantRequest,
    RegisterTenantResponse,
    UserSummary,
)
from app.modules.auth.service import AuthService


class AuthUseCase:
    """Entry point for the auth module's own router. Delegates to AuthService."""

    def __init__(self, service: AuthService) -> None:
        self._service = service

    async def register_tenant(
        self, payload: RegisterTenantRequest
    ) -> RegisterTenantResponse:
        return await self._service.register_tenant(payload)

    async def create_user(
        self, payload: CreateUserRequest, actor_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> AuthUserResponse:
        return await self._service.create_user(payload, actor_id, tenant_id)

    async def invite_user(
        self, payload: InviteUserRequest, actor_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> None:
        await self._service.invite_user(payload, actor_id, tenant_id)

    async def accept_invite(self, payload: AcceptInviteRequest) -> AuthUserResponse:
        return await self._service.accept_invite(payload)

    async def login(
        self,
        payload: LoginRequest,
        tenant_slug: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> tuple[AuthUserResponse, str, str]:
        return await self._service.login(payload, tenant_slug, ip_address, user_agent)

    async def logout(self, refresh_token: str | None) -> None:
        await self._service.logout(refresh_token)

    async def get_me(self, user_id: uuid.UUID) -> MeResponse:
        return await self._service.get_me(user_id)

    async def user_exists(self, tenant_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        return await self._service.user_exists(tenant_id, user_id)

    async def search_users(
        self, tenant_id: uuid.UUID, query: str, limit: int = 20
    ) -> list[UserSummary]:
        return await self._service.search_users(tenant_id, query, limit)

    async def lookup_users(
        self, tenant_id: uuid.UUID, ids: list[uuid.UUID]
    ) -> list[UserSummary]:
        return await self._service.lookup_users(tenant_id, ids)
