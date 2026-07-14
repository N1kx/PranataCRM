import hashlib
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import RefreshToken, Role, Tenant, User, UserRole
from app.modules.licensing.models import App, AppSeat, AppSubscription
from app.shared.types import BillingPlan, SeatStatus, SuiteRole, SubscriptionStatus


class AuthRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Tenant ────────────────────────────────────────────────────────────────

    async def get_tenant_by_slug(self, slug: str) -> Tenant | None:
        result = await self._session.execute(
            select(Tenant).where(Tenant.slug == slug)
        )
        return result.scalar_one_or_none()

    async def create_tenant(self, *, name: str, slug: str) -> Tenant:
        tenant = Tenant(name=name, slug=slug, plan=BillingPlan.FREE)
        self._session.add(tenant)
        await self._session.flush()
        return tenant

    # ── User ──────────────────────────────────────────────────────────────────

    async def get_user_by_email(self, tenant_id: uuid.UUID, email: str) -> User | None:
        result = await self._session.execute(
            select(User).where(User.tenant_id == tenant_id, User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self._session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_user(
        self,
        *,
        tenant_id: uuid.UUID,
        email: str,
        hashed_password: str,
        full_name: str,
        suite_role: str = SuiteRole.MEMBER,
        created_by: uuid.UUID | None = None,
    ) -> User:
        user = User(
            tenant_id=tenant_id,
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            suite_role=suite_role,
            is_active=True,
            created_by=created_by,
        )
        self._session.add(user)
        await self._session.flush()
        return user

    async def update_last_login(self, user_id: uuid.UUID) -> None:
        await self._session.execute(
            update(User)
            .where(User.id == user_id)
            .values(last_login_at=datetime.now(timezone.utc))
        )

    async def search_users(
        self, tenant_id: uuid.UUID, query: str, limit: int = 20
    ) -> list[User]:
        stmt = select(User).where(
            User.tenant_id == tenant_id,
            User.is_active.is_(True),
        )
        q = (query or "").strip()
        if q:
            # Escape LIKE wildcards so a term such as "50%" or "a_b" matches those
            # characters literally instead of acting as a pattern.
            escaped = q.lower().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            like = f"%{escaped}%"
            stmt = stmt.where(
                func.lower(User.full_name).like(like, escape="\\")
                | func.lower(User.email).like(like, escape="\\")
            )
        stmt = stmt.order_by(User.full_name).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_users_by_ids(
        self, tenant_id: uuid.UUID, ids: list[uuid.UUID]
    ) -> list[User]:
        if not ids:
            return []
        result = await self._session.execute(
            select(User).where(User.tenant_id == tenant_id, User.id.in_(ids))
        )
        return list(result.scalars().all())

    # ── Licensing helpers ─────────────────────────────────────────────────────

    async def get_app_by_code(self, code: str) -> App | None:
        result = await self._session.execute(
            select(App).where(App.code == code, App.is_active.is_(True))
        )
        return result.scalar_one_or_none()

    async def create_app_subscription(
        self,
        *,
        tenant_id: uuid.UUID,
        app_id: uuid.UUID,
        seats_purchased: int = 3,
    ) -> AppSubscription:
        sub = AppSubscription(
            tenant_id=tenant_id,
            app_id=app_id,
            plan=BillingPlan.FREE,
            seats_purchased=seats_purchased,
            status=SubscriptionStatus.ACTIVE,
        )
        self._session.add(sub)
        await self._session.flush()
        return sub

    async def count_active_seats(self, subscription_id: uuid.UUID) -> int:
        from sqlalchemy import func
        result = await self._session.execute(
            select(func.count()).select_from(AppSeat).where(
                AppSeat.subscription_id == subscription_id,
                AppSeat.status == SeatStatus.ACTIVE,
            )
        )
        return result.scalar_one()

    async def create_app_seat(
        self,
        *,
        tenant_id: uuid.UUID,
        subscription_id: uuid.UUID,
        app_id: uuid.UUID,
        user_id: uuid.UUID,
        created_by: uuid.UUID | None = None,
    ) -> AppSeat:
        seat = AppSeat(
            tenant_id=tenant_id,
            subscription_id=subscription_id,
            app_id=app_id,
            user_id=user_id,
            status=SeatStatus.ACTIVE,
            created_by=created_by,
        )
        self._session.add(seat)
        await self._session.flush()
        return seat

    async def get_or_create_admin_role(
        self, *, app_id: uuid.UUID, tenant_id: uuid.UUID | None = None
    ) -> Role:
        result = await self._session.execute(
            select(Role).where(
                Role.app_id == app_id,
                Role.name == "Administrator",
                Role.is_system.is_(True),
            )
        )
        role = result.scalar_one_or_none()
        if role is None:
            role = Role(
                app_id=app_id,
                tenant_id=tenant_id,
                name="Administrator",
                is_system=True,
            )
            self._session.add(role)
            await self._session.flush()
        return role

    async def get_role_by_id(self, role_id: uuid.UUID) -> Role | None:
        result = await self._session.execute(
            select(Role).where(Role.id == role_id)
        )
        return result.scalar_one_or_none()

    async def create_user_role(
        self,
        *,
        tenant_id: uuid.UUID,
        app_seat_id: uuid.UUID,
        role_id: uuid.UUID,
        created_by: uuid.UUID | None = None,
    ) -> UserRole:
        user_role = UserRole(
            tenant_id=tenant_id,
            app_seat_id=app_seat_id,
            role_id=role_id,
            created_by=created_by,
        )
        self._session.add(user_role)
        await self._session.flush()
        return user_role

    # ── Refresh token ─────────────────────────────────────────────────────────

    @staticmethod
    def hash_token(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    async def store_refresh_token(
        self,
        *,
        user_id: uuid.UUID,
        token: str,
        expires_at: datetime,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        rt = RefreshToken(
            user_id=user_id,
            token_hash=self.hash_token(token),
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self._session.add(rt)
        await self._session.flush()

    async def revoke_refresh_token(self, token: str) -> None:
        token_hash = self.hash_token(token)
        await self._session.execute(
            update(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .values(revoked=True)
        )

    async def get_refresh_token(self, token: str) -> RefreshToken | None:
        token_hash = self.hash_token(token)
        result = await self._session.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked.is_(False),
            )
        )
        return result.scalar_one_or_none()
