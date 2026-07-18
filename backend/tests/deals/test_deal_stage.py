import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, patch

from tests.deals.base import DealsTestCase
from tests.deals.test_deals import _fake_deal


class DealStageTests(DealsTestCase):
    """PATCH /deals/{id}/stage — the only way to change a deal's stage."""

    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        self._tenant_id = uuid.uuid4()
        self._user_id = uuid.uuid4()
        self._deal_id = uuid.uuid4()

    def _override_current_user(self):
        from app.main import app
        from app.modules.auth.dependencies import CurrentUser, get_current_user

        async def _override():
            return CurrentUser(
                user_id=self._user_id, tenant_id=self._tenant_id, suite_role="tenant_owner"
            )

        app.dependency_overrides[get_current_user] = _override
        return app

    def _clear_override(self, app):
        from app.modules.auth.dependencies import get_current_user
        app.dependency_overrides.pop(get_current_user, None)

    @patch("app.modules.deals.repository.DealRepository.update", new_callable=AsyncMock)
    @patch("app.modules.deals.repository.DealRepository.get_by_id", new_callable=AsyncMock)
    async def test_stage_to_won_sets_status_probability_and_close_date(
        self, mock_get, mock_update
    ):
        mock_get.return_value = _fake_deal(
            self._deal_id, self._tenant_id,
            stage="proposal", status="open", value=Decimal("500"), probability=50,
        )
        mock_update.return_value = _fake_deal(
            self._deal_id, self._tenant_id, stage="won", status="won", probability=100,
        )
        app = self._override_current_user()
        try:
            resp = await self.client.patch(
                f"/api/v1/deals/{self._deal_id}/stage", json={"stage": "won"}
            )
        finally:
            self._clear_override(app)

        self.assertEqual(resp.status_code, 200)
        call_data = mock_update.call_args.args[1]
        self.assertEqual(call_data["status"], "won")
        self.assertEqual(call_data["probability"], 100)
        self.assertIsNotNone(call_data["actual_close_date"])
        self.assertEqual(call_data["weighted_value"], Decimal("500.00"))

    @patch("app.modules.deals.repository.DealRepository.get_by_id", new_callable=AsyncMock)
    async def test_stage_to_lost_without_lost_reason_returns_422(self, mock_get):
        mock_get.return_value = _fake_deal(self._deal_id, self._tenant_id, stage="proposal")
        app = self._override_current_user()
        try:
            resp = await self.client.patch(
                f"/api/v1/deals/{self._deal_id}/stage", json={"stage": "lost"}
            )
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)
        self.assertEqual(resp.json()["error"]["code"], "INVALID_STAGE_TRANSITION")

    @patch("app.modules.deals.repository.DealRepository.update", new_callable=AsyncMock)
    @patch("app.modules.deals.repository.DealRepository.get_by_id", new_callable=AsyncMock)
    async def test_stage_to_lost_with_lost_reason_succeeds(self, mock_get, mock_update):
        mock_get.return_value = _fake_deal(self._deal_id, self._tenant_id, stage="proposal")
        mock_update.return_value = _fake_deal(
            self._deal_id, self._tenant_id, stage="lost", status="lost",
        )
        app = self._override_current_user()
        try:
            resp = await self.client.patch(
                f"/api/v1/deals/{self._deal_id}/stage",
                json={"stage": "lost", "lost_reason": "Went with a competitor"},
            )
        finally:
            self._clear_override(app)

        self.assertEqual(resp.status_code, 200)
        call_data = mock_update.call_args.args[1]
        self.assertEqual(call_data["status"], "lost")
        self.assertEqual(call_data["probability"], 0)
        self.assertEqual(call_data["lost_reason"], "Went with a competitor")

    @patch("app.modules.deals.repository.DealRepository.update", new_callable=AsyncMock)
    @patch("app.modules.deals.repository.DealRepository.get_by_id", new_callable=AsyncMock)
    async def test_reopen_from_lost_clears_actual_close_date_and_sets_open(
        self, mock_get, mock_update
    ):
        import datetime as dt

        mock_get.return_value = _fake_deal(
            self._deal_id, self._tenant_id,
            stage="lost", status="lost", actual_close_date=dt.date(2026, 1, 1),
        )
        mock_update.return_value = _fake_deal(
            self._deal_id, self._tenant_id, stage="qualified", status="open",
        )
        app = self._override_current_user()
        try:
            resp = await self.client.patch(
                f"/api/v1/deals/{self._deal_id}/stage", json={"stage": "qualified"}
            )
        finally:
            self._clear_override(app)

        self.assertEqual(resp.status_code, 200)
        call_data = mock_update.call_args.args[1]
        self.assertEqual(call_data["status"], "open")
        self.assertIsNone(call_data["actual_close_date"])

    @patch("app.modules.deals.repository.DealRepository.update", new_callable=AsyncMock)
    @patch("app.modules.deals.repository.DealRepository.get_by_id", new_callable=AsyncMock)
    async def test_same_stage_is_a_noop(self, mock_get, mock_update):
        mock_get.return_value = _fake_deal(self._deal_id, self._tenant_id, stage="proposal")
        app = self._override_current_user()
        try:
            resp = await self.client.patch(
                f"/api/v1/deals/{self._deal_id}/stage", json={"stage": "proposal"}
            )
        finally:
            self._clear_override(app)

        self.assertEqual(resp.status_code, 200)
        mock_update.assert_not_called()

    @patch("app.modules.deals.repository.DealRepository.get_by_id", new_callable=AsyncMock)
    async def test_abandoned_deal_rejects_stage_change(self, mock_get):
        mock_get.return_value = _fake_deal(
            self._deal_id, self._tenant_id, stage="lead", status="abandoned",
        )
        app = self._override_current_user()
        try:
            resp = await self.client.patch(
                f"/api/v1/deals/{self._deal_id}/stage", json={"stage": "qualified"}
            )
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)
        self.assertEqual(resp.json()["error"]["code"], "INVALID_STAGE_TRANSITION")

    async def test_stage_invalid_value_returns_422(self):
        app = self._override_current_user()
        try:
            resp = await self.client.patch(
                f"/api/v1/deals/{self._deal_id}/stage", json={"stage": "bogus"}
            )
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)

    @patch("app.modules.deals.repository.DealRepository.get_by_id", new_callable=AsyncMock)
    async def test_stage_endpoint_not_found_returns_404(self, mock_get):
        mock_get.return_value = None
        app = self._override_current_user()
        try:
            resp = await self.client.patch(
                f"/api/v1/deals/{self._deal_id}/stage", json={"stage": "qualified"}
            )
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 404)
