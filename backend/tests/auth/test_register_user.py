import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from tests.auth.base import AuthTestCase


def _make_access_cookie(user_id: uuid.UUID, tenant_id: uuid.UUID) -> str:
    from app.shared.jwt import create_access_token
    return create_access_token(str(user_id), str(tenant_id))


def _fake_user(
    user_id: uuid.UUID | None = None,
    tenant_id: uuid.UUID | None = None,
    email: str = "niko@nxcorp.co",
    suite_role: str = "tenant_owner",
) -> SimpleNamespace:
    from app.shared.security import hash_password
    return SimpleNamespace(
        id=user_id or uuid.uuid4(),
        tenant_id=tenant_id or uuid.uuid4(),
        email=email,
        full_name="Niko Winoko",
        hashed_password=hash_password("secret123"),
        suite_role=suite_role,
        is_active=True,
        created_by=None,
    )


class CreateUserTests(AuthTestCase):

    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        self._tenant_id = uuid.uuid4()
        self._owner_id = uuid.uuid4()
        self._owner = _fake_user(
            user_id=self._owner_id,
            tenant_id=self._tenant_id,
            suite_role="tenant_owner",
        )
        token = _make_access_cookie(self._owner_id, self._tenant_id)
        self.client.cookies.set("access_token", token)

    @patch("app.modules.auth.router.get_current_user")
    @patch("app.modules.auth.repository.AuthRepository.get_user_by_email", new_callable=AsyncMock)
    @patch("app.modules.auth.repository.AuthRepository.get_app_by_code", new_callable=AsyncMock)
    @patch("app.modules.auth.repository.AuthRepository.create_user", new_callable=AsyncMock)
    async def test_owner_creates_user(
        self, mock_create, mock_get_app, mock_get_email, mock_current_user
    ):
        from app.modules.auth.router import CurrentUser
        mock_current_user.return_value = CurrentUser(
            user_id=self._owner_id,
            tenant_id=self._tenant_id,
            suite_role="tenant_owner",
        )
        mock_get_email.return_value = None
        mock_get_app.return_value = None
        new_user = _fake_user(tenant_id=self._tenant_id, email="member1@nxcorp.co", suite_role="member")
        mock_create.return_value = new_user

        resp = await self.client.post("/api/v1/users", json={
            "full_name": "Member One",
            "email": "member1@nxcorp.co",
            "password": "secret123",
            "role_id": str(uuid.uuid4()),
        }, headers={"X-Tenant-Slug": "nxcorp"})
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.json()["email"], "member1@nxcorp.co")

    @patch("app.modules.auth.router.get_current_user")
    @patch("app.modules.auth.repository.AuthRepository.get_user_by_email", new_callable=AsyncMock)
    async def test_duplicate_email_rejected(self, mock_get_email, mock_current_user):
        from app.modules.auth.router import CurrentUser
        mock_current_user.return_value = CurrentUser(
            user_id=self._owner_id,
            tenant_id=self._tenant_id,
            suite_role="tenant_owner",
        )
        mock_get_email.return_value = self._owner  # already exists

        resp = await self.client.post("/api/v1/users", json={
            "full_name": "Dupe",
            "email": "niko@nxcorp.co",
            "password": "secret123",
            "role_id": str(uuid.uuid4()),
        }, headers={"X-Tenant-Slug": "nxcorp"})
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.json()["error"]["code"], "AUTH_EMAIL_EXISTS")

    @patch("app.modules.auth.router.get_current_user")
    async def test_member_cannot_create_user(self, mock_current_user):
        from app.modules.auth.router import CurrentUser
        mock_current_user.return_value = CurrentUser(
            user_id=self._owner_id,
            tenant_id=self._tenant_id,
            suite_role="member",
        )
        resp = await self.client.post("/api/v1/users", json={
            "full_name": "Unauthorized",
            "email": "hack@nxcorp.co",
            "password": "secret123",
            "role_id": str(uuid.uuid4()),
        }, headers={"X-Tenant-Slug": "nxcorp"})
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.json()["error"]["code"], "AUTH_PERMISSION_DENIED")
