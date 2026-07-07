import uuid
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db as get_session
from app.modules.auth.exceptions import NotAuthenticated
from app.modules.auth.repository import AuthRepository
from app.shared.jwt import decode_token
from app.shared.logging import bind_user_id


class CurrentUser:
    def __init__(self, user_id: uuid.UUID, tenant_id: uuid.UUID, suite_role: str) -> None:
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.suite_role = suite_role


async def get_current_user(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CurrentUser:
    token = request.cookies.get("access_token")
    if not token:
        raise NotAuthenticated()
    claims = decode_token(token)
    if claims is None or claims.get("type") != "access":
        raise NotAuthenticated()

    repo = AuthRepository(session)
    user = await repo.get_user_by_id(uuid.UUID(claims["sub"]))
    if user is None or not user.is_active:
        raise NotAuthenticated()

    bind_user_id(str(user.id))
    request.state.user_id = str(user.id)

    return CurrentUser(
        user_id=user.id,
        tenant_id=user.tenant_id,
        suite_role=user.suite_role,
    )
