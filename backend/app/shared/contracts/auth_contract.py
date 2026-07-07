import uuid
from typing import Protocol

# Re-exported so other modules depend on auth's request dependency through the
# contract layer instead of importing app.modules.auth internals directly.
# Unlike AuthContractProtocol below, this is a concrete re-export because
# FastAPI's Depends() needs a real callable, not a Protocol.
from app.modules.auth.dependencies import CurrentUser, get_current_user
from app.modules.auth.schemas import (
    AcceptInviteRequest,
    AuthUserResponse,
    CreateUserRequest,
    InviteUserRequest,
    LoginRequest,
    RegisterTenantRequest,
    RegisterTenantResponse,
)

__all__ = [
    "AuthContractProtocol",
    "CurrentUser",
    "get_current_user",
]


class AuthContractProtocol(Protocol):
    async def register_tenant(
        self, payload: RegisterTenantRequest
    ) -> RegisterTenantResponse: ...

    async def create_user(
        self, payload: CreateUserRequest, actor_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> AuthUserResponse: ...

    async def invite_user(
        self, payload: InviteUserRequest, actor_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> None: ...

    async def accept_invite(self, payload: AcceptInviteRequest) -> AuthUserResponse: ...

    async def login(
        self,
        payload: LoginRequest,
        tenant_slug: str,
        ip_address: str | None,
        user_agent: str | None,
    ) -> tuple[AuthUserResponse, str, str]: ...

    async def logout(self, refresh_token: str | None) -> None: ...
