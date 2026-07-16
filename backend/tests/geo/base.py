import uuid

from tests.common import MockedAppTestCase


class GeoTestCase(MockedAppTestCase):
    """Base for async geo tests. Redis and DB are mocked."""

    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        self._tenant_id = uuid.uuid4()
        self._user_id = uuid.uuid4()

    def _override_current_user(self, suite_role: str = "member"):
        from app.main import app
        from app.modules.auth.dependencies import CurrentUser, get_current_user

        async def _override():
            return CurrentUser(
                user_id=self._user_id, tenant_id=self._tenant_id, suite_role=suite_role
            )

        app.dependency_overrides[get_current_user] = _override
        return app

    def _clear_override(self, app):
        from app.modules.auth.dependencies import get_current_user
        app.dependency_overrides.pop(get_current_user, None)
