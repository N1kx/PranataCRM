import uuid
from typing import Protocol

# Re-exported so other modules depend on auth's request dependency through the
# contract layer instead of importing app.modules.auth internals directly.
from app.modules.auth.dependencies import CurrentUser, get_current_user

__all__ = [
    "AuthContractProtocol",
    "CurrentUser",
    "get_current_user",
]


class AuthContractProtocol(Protocol):
    async def user_exists(self, tenant_id: uuid.UUID, user_id: uuid.UUID) -> bool: ...
