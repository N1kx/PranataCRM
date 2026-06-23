"""Internal domain logic for auth. Never imported from outside this module."""
import uuid
from datetime import datetime, timedelta, timezone

import resend

from app.config import get_settings
from app.modules.auth.exceptions import (
    EmailAlreadyExists,
    InvalidCredentials,
    PermissionDenied,
    SeatLimitReached,
    SlugAlreadyTaken,
    TenantNotFound,
    InviteInvalidOrExpired,
)
from app.modules.auth.repository import AuthRepository
from app.modules.auth.schemas import (
    AcceptInviteRequest,
    AuthUserResponse,
    CreateUserRequest,
    InviteUserRequest,
    LoginRequest,
    RegisterTenantRequest,
    RegisterTenantResponse,
)
from app.shared.jwt import create_access_token, create_refresh_token, decode_token
from app.shared.security import hash_password, verify_password
from app.shared.types import SuiteRole

_CRM_APP_CODE = "crm"


async def send_invite_email(to_email: str, slug: str, token: str) -> None:
    settings = get_settings()
    resend.api_key = settings.resend_api_key
    link = f"https://{slug}.pranata.app/accept-invite?token={token}"
    resend.Emails.send({
        "from": settings.email_from,
        "to": [to_email],
        "subject": "You've been invited to PranataCRM",
        "html": f'<p>Click <a href="{link}">here</a> to accept your invitation.</p>',
    })


class AuthService:
    def __init__(self, repo: AuthRepository) -> None:
        self._repo = repo

    async def register_tenant(
        self, payload: RegisterTenantRequest
    ) -> RegisterTenantResponse:
        if await self._repo.get_tenant_by_slug(payload.slug):
            raise SlugAlreadyTaken()

        tenant = await self._repo.create_tenant(
            name=payload.organization_name, slug=payload.slug
        )

        user = await self._repo.create_user(
            tenant_id=tenant.id,
            email=payload.email,
            hashed_password=hash_password(payload.password),
            full_name=payload.full_name,
            suite_role=SuiteRole.TENANT_OWNER,
        )
        # Set audit field now that we have user.id
        user.created_by = user.id

        crm_app = await self._repo.get_app_by_code(_CRM_APP_CODE)
        if crm_app is not None:
            sub = await self._repo.create_app_subscription(
                tenant_id=tenant.id,
                app_id=crm_app.id,
                seats_purchased=3,
            )
            seat = await self._repo.create_app_seat(
                tenant_id=tenant.id,
                subscription_id=sub.id,
                app_id=crm_app.id,
                user_id=user.id,
                created_by=user.id,
            )
            role = await self._repo.get_or_create_admin_role(
                app_id=crm_app.id, tenant_id=tenant.id
            )
            await self._repo.create_user_role(
                tenant_id=tenant.id,
                app_seat_id=seat.id,
                role_id=role.id,
                created_by=user.id,
            )

        return RegisterTenantResponse(
            tenant_id=str(tenant.id),
            slug=tenant.slug,
            user=AuthUserResponse(
                id=str(user.id),
                email=user.email,
                full_name=user.full_name,
                suite_role=user.suite_role,
            ),
        )

    async def create_user(
        self, payload: CreateUserRequest, actor_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> AuthUserResponse:
        if await self._repo.get_user_by_email(tenant_id, payload.email):
            raise EmailAlreadyExists()

        crm_app = await self._repo.get_app_by_code(_CRM_APP_CODE)
        role_uuid = uuid.UUID(payload.role_id)

        if crm_app is not None:
            sub = await self._get_active_subscription(tenant_id, crm_app.id)
            if sub is not None:
                active_seats = await self._repo.count_active_seats(sub.id)
                if active_seats >= sub.seats_purchased:
                    raise SeatLimitReached()

        user = await self._repo.create_user(
            tenant_id=tenant_id,
            email=payload.email,
            hashed_password=hash_password(payload.password),
            full_name=payload.full_name,
            suite_role=SuiteRole.MEMBER,
            created_by=actor_id,
        )

        if crm_app is not None:
            sub = await self._get_active_subscription(tenant_id, crm_app.id)
            if sub is not None:
                seat = await self._repo.create_app_seat(
                    tenant_id=tenant_id,
                    subscription_id=sub.id,
                    app_id=crm_app.id,
                    user_id=user.id,
                    created_by=actor_id,
                )
                await self._repo.create_user_role(
                    tenant_id=tenant_id,
                    app_seat_id=seat.id,
                    role_id=role_uuid,
                    created_by=actor_id,
                )

        return AuthUserResponse(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            suite_role=user.suite_role,
        )

    async def invite_user(
        self, payload: InviteUserRequest, actor_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> None:
        if await self._repo.get_user_by_email(tenant_id, payload.email):
            raise EmailAlreadyExists()

        tenant = await self._get_tenant_by_id(tenant_id)

        # Encode invite as JWT with purpose='invite'
        from app.config import get_settings
        import jwt as _jwt
        settings = get_settings()
        from datetime import datetime, timedelta, timezone
        now = datetime.now(timezone.utc)
        token = _jwt.encode(
            {
                "purpose": "invite",
                "email": payload.email,
                "full_name": payload.full_name,
                "role_id": payload.role_id,
                "tid": str(tenant_id),
                "inv_by": str(actor_id),
                "iat": now,
                "exp": now + timedelta(days=7),
            },
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )

        await send_invite_email(payload.email, tenant.slug, token)

    async def accept_invite(self, payload: AcceptInviteRequest) -> AuthUserResponse:
        from app.shared.jwt import decode_token
        claims = decode_token(payload.token)
        if claims is None or claims.get("purpose") != "invite":
            raise InviteInvalidOrExpired()

        email: str = claims["email"]
        role_id: str = claims["role_id"]
        tenant_id = uuid.UUID(claims["tid"])
        actor_id = uuid.UUID(claims["inv_by"])

        if await self._repo.get_user_by_email(tenant_id, email):
            raise EmailAlreadyExists()

        crm_app = await self._repo.get_app_by_code(_CRM_APP_CODE)
        if crm_app is not None:
            sub = await self._get_active_subscription(tenant_id, crm_app.id)
            if sub is not None:
                active_seats = await self._repo.count_active_seats(sub.id)
                if active_seats >= sub.seats_purchased:
                    raise SeatLimitReached()

        user = await self._repo.create_user(
            tenant_id=tenant_id,
            email=email,
            hashed_password=hash_password(payload.password),
            full_name=payload.full_name,
            suite_role=SuiteRole.MEMBER,
            created_by=actor_id,
        )

        if crm_app is not None:
            sub = await self._get_active_subscription(tenant_id, crm_app.id)
            if sub is not None:
                seat = await self._repo.create_app_seat(
                    tenant_id=tenant_id,
                    subscription_id=sub.id,
                    app_id=crm_app.id,
                    user_id=user.id,
                    created_by=actor_id,
                )
                await self._repo.create_user_role(
                    tenant_id=tenant_id,
                    app_seat_id=seat.id,
                    role_id=uuid.UUID(role_id),
                    created_by=actor_id,
                )

        return AuthUserResponse(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            suite_role=user.suite_role,
        )

    async def login(
        self,
        payload: LoginRequest,
        tenant_slug: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> tuple[AuthUserResponse, str, str]:
        tenant = await self._repo.get_tenant_by_slug(tenant_slug)
        if tenant is None:
            raise TenantNotFound()

        user = await self._repo.get_user_by_email(tenant.id, payload.email)
        if user is None or not verify_password(payload.password, user.hashed_password) or not user.is_active:
            raise InvalidCredentials()

        access_token = create_access_token(str(user.id), str(tenant.id))
        refresh_token, _jti = create_refresh_token(str(user.id), str(tenant.id))

        settings = get_settings()
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.jwt_refresh_token_expire_days
        )
        await self._repo.store_refresh_token(
            user_id=user.id,
            token=refresh_token,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self._repo.update_last_login(user.id)

        return (
            AuthUserResponse(
                id=str(user.id),
                email=user.email,
                full_name=user.full_name,
                suite_role=user.suite_role,
            ),
            access_token,
            refresh_token,
        )

    async def logout(self, refresh_token: str | None) -> None:
        if refresh_token:
            await self._repo.revoke_refresh_token(refresh_token)

    async def get_current_user_from_token(
        self, access_token: str
    ) -> tuple[uuid.UUID, uuid.UUID]:
        from app.modules.auth.exceptions import NotAuthenticated
        claims = decode_token(access_token)
        if claims is None or claims.get("type") != "access":
            raise NotAuthenticated()
        return uuid.UUID(claims["sub"]), uuid.UUID(claims["tid"])

    # ── Private helpers ───────────────────────────────────────────────────────

    async def _get_tenant_by_id(self, tenant_id: uuid.UUID):
        from sqlalchemy import select
        from app.modules.auth.models import Tenant
        result = await self._repo._session.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        return result.scalar_one_or_none()

    async def _get_active_subscription(self, tenant_id: uuid.UUID, app_id: uuid.UUID):
        from sqlalchemy import select
        from app.modules.licensing.models import AppSubscription
        result = await self._repo._session.execute(
            select(AppSubscription).where(
                AppSubscription.tenant_id == tenant_id,
                AppSubscription.app_id == app_id,
            )
        )
        return result.scalar_one_or_none()

    def _check_can_manage_users(self, suite_role: str) -> None:
        if suite_role not in (SuiteRole.TENANT_OWNER, SuiteRole.TENANT_ADMIN):
            raise PermissionDenied()
