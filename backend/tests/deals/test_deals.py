import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from tests.deals.base import DealsTestCase


def _fake_deal(
    deal_id: uuid.UUID,
    tenant_id: uuid.UUID,
    title: str = "Big Sale",
    **overrides,
) -> SimpleNamespace:
    defaults = dict(
        id=deal_id,
        tenant_id=tenant_id,
        contact_id=None,
        company_id=None,
        owner_id=None,
        title=title,
        description=None,
        stage="lead",
        status="open",
        deal_type=None,
        value=Decimal("0"),
        currency="IDR",
        probability=0,
        weighted_value=Decimal("0.00"),
        expected_close_date=date(2026, 12, 31),
        actual_close_date=None,
        stage_changed_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        priority=None,
        source=None,
        next_step=None,
        next_step_date=None,
        competitor=None,
        close_reason=None,
        lost_reason=None,
        tags=[],
        custom_fields={},
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class DealsTests(DealsTestCase):

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

    # ── create ────────────────────────────────────────────────────────────────

    @patch("app.modules.deals.repository.DealRepository.create", new_callable=AsyncMock)
    async def test_create_deal_success_with_defaults(self, mock_create):
        mock_create.return_value = _fake_deal(self._deal_id, self._tenant_id)
        app = self._override_current_user()
        try:
            resp = await self.client.post(
                "/api/v1/deals",
                json={"title": "Big Sale", "expected_close_date": "2026-12-31"},
            )
        finally:
            self._clear_override(app)

        self.assertEqual(resp.status_code, 201)
        body = resp.json()
        self.assertEqual(body["title"], "Big Sale")
        self.assertEqual(body["stage"], "lead")
        self.assertEqual(body["status"], "open")
        self.assertEqual(body["currency"], "IDR")
        self.assertEqual(body["value"], "0")
        self.assertEqual(body["probability"], 0)
        self.assertEqual(body["weighted_value"], "0.00")

        call_data = mock_create.call_args.args[0]
        self.assertEqual(call_data["tenant_id"], self._tenant_id)
        self.assertEqual(call_data["created_by"], self._user_id)
        self.assertEqual(call_data["status"], "open")
        self.assertEqual(call_data["stage"], "lead")
        self.assertEqual(call_data["weighted_value"], Decimal("0.00"))

    async def test_create_deal_without_expected_close_date_returns_422(self):
        app = self._override_current_user()
        try:
            resp = await self.client.post("/api/v1/deals", json={"title": "Big Sale"})
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)

    async def test_create_deal_blank_title_returns_422(self):
        app = self._override_current_user()
        try:
            resp = await self.client.post(
                "/api/v1/deals",
                json={"title": "   ", "expected_close_date": "2026-12-31"},
            )
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)

    async def test_create_deal_invalid_stage_returns_422(self):
        app = self._override_current_user()
        try:
            resp = await self.client.post(
                "/api/v1/deals",
                json={
                    "title": "Big Sale", "expected_close_date": "2026-12-31",
                    "stage": "bogus",
                },
            )
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)

    async def test_create_deal_status_field_ignored(self):
        # status is server-derived; DealCreate has no status field at all, so
        # an extra "status" key is silently dropped rather than applied.
        mock_create_deal = _fake_deal(self._deal_id, self._tenant_id)
        with patch(
            "app.modules.deals.repository.DealRepository.create",
            new_callable=AsyncMock,
            return_value=mock_create_deal,
        ) as mock_create:
            app = self._override_current_user()
            try:
                resp = await self.client.post(
                    "/api/v1/deals",
                    json={
                        "title": "Big Sale", "expected_close_date": "2026-12-31",
                        "status": "won",
                    },
                )
            finally:
                self._clear_override(app)
            self.assertEqual(resp.status_code, 201)
            call_data = mock_create.call_args.args[0]
            self.assertEqual(call_data["status"], "open")

    @patch("app.modules.deals.repository.DealRepository.create", new_callable=AsyncMock)
    async def test_create_deal_computes_weighted_value(self, mock_create):
        mock_create.return_value = _fake_deal(
            self._deal_id, self._tenant_id,
            value=Decimal("1000000"), probability=40, weighted_value=Decimal("400000.00"),
        )
        app = self._override_current_user()
        try:
            resp = await self.client.post(
                "/api/v1/deals",
                json={
                    "title": "Big Sale", "expected_close_date": "2026-12-31",
                    "value": "1000000", "probability": 40,
                },
            )
        finally:
            self._clear_override(app)

        self.assertEqual(resp.status_code, 201)
        call_data = mock_create.call_args.args[0]
        self.assertEqual(call_data["weighted_value"], Decimal("400000.00"))

    # ── get ───────────────────────────────────────────────────────────────────

    @patch("app.modules.deals.repository.DealRepository.get_by_id", new_callable=AsyncMock)
    async def test_get_deal_success(self, mock_get):
        mock_get.return_value = _fake_deal(self._deal_id, self._tenant_id)
        app = self._override_current_user()
        try:
            resp = await self.client.get(f"/api/v1/deals/{self._deal_id}")
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["id"], str(self._deal_id))

    @patch("app.modules.deals.repository.DealRepository.get_by_id", new_callable=AsyncMock)
    async def test_get_deal_not_found_returns_404(self, mock_get):
        mock_get.return_value = None
        app = self._override_current_user()
        try:
            resp = await self.client.get(f"/api/v1/deals/{self._deal_id}")
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json()["error"]["code"], "DEAL_NOT_FOUND")

    # ── list ──────────────────────────────────────────────────────────────────

    @patch("app.modules.deals.repository.DealRepository.list", new_callable=AsyncMock)
    async def test_list_deals_defaults(self, mock_list):
        mock_list.return_value = ([_fake_deal(self._deal_id, self._tenant_id)], 1)
        app = self._override_current_user()
        try:
            resp = await self.client.get("/api/v1/deals")
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["total"], 1)
        self.assertEqual(body["page"], 1)
        self.assertEqual(body["page_size"], 20)

    async def test_list_deals_invalid_stage_returns_422(self):
        app = self._override_current_user()
        try:
            resp = await self.client.get("/api/v1/deals", params={"stage": "bogus"})
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)
        self.assertEqual(resp.json()["error"]["code"], "VALIDATION_ERROR")

    async def test_list_deals_invalid_sort_returns_422(self):
        app = self._override_current_user()
        try:
            resp = await self.client.get("/api/v1/deals", params={"sort": "bogus"})
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)

    async def test_list_deals_invalid_company_id_returns_422(self):
        app = self._override_current_user()
        try:
            resp = await self.client.get("/api/v1/deals", params={"company_id": "not-a-uuid"})
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)

    @patch("app.modules.deals.repository.DealRepository.list", new_callable=AsyncMock)
    async def test_list_deals_page_size_capped(self, mock_list):
        mock_list.return_value = ([], 0)
        app = self._override_current_user()
        try:
            resp = await self.client.get("/api/v1/deals", params={"page_size": 500})
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["page_size"], 100)
        self.assertEqual(mock_list.call_args.args[1], 100)

    @patch("app.modules.deals.repository.DealRepository.list", new_callable=AsyncMock)
    async def test_list_deals_filters_by_company_id(self, mock_list):
        mock_list.return_value = ([], 0)
        company_id = uuid.uuid4()
        app = self._override_current_user()
        try:
            resp = await self.client.get(
                "/api/v1/deals", params={"company_id": str(company_id)}
            )
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(mock_list.call_args.kwargs["company_id"], company_id)

    # ── update ────────────────────────────────────────────────────────────────

    @patch("app.modules.deals.repository.DealRepository.update", new_callable=AsyncMock)
    @patch("app.modules.deals.repository.DealRepository.get_by_id", new_callable=AsyncMock)
    async def test_update_deal_success(self, mock_get, mock_update):
        mock_get.return_value = _fake_deal(self._deal_id, self._tenant_id)
        mock_update.return_value = _fake_deal(
            self._deal_id, self._tenant_id, title="Renamed"
        )
        app = self._override_current_user()
        try:
            resp = await self.client.patch(
                f"/api/v1/deals/{self._deal_id}", json={"title": "Renamed"}
            )
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["title"], "Renamed")

    @patch("app.modules.deals.repository.DealRepository.get_by_id", new_callable=AsyncMock)
    async def test_update_deal_null_expected_close_date_returns_422(self, mock_get):
        mock_get.return_value = _fake_deal(self._deal_id, self._tenant_id)
        app = self._override_current_user()
        try:
            resp = await self.client.patch(
                f"/api/v1/deals/{self._deal_id}", json={"expected_close_date": None}
            )
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)

    @patch("app.modules.deals.repository.DealRepository.get_by_id", new_callable=AsyncMock)
    async def test_update_deal_not_found_returns_404(self, mock_get):
        mock_get.return_value = None
        app = self._override_current_user()
        try:
            resp = await self.client.patch(
                f"/api/v1/deals/{self._deal_id}", json={"title": "Renamed"}
            )
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 404)

    @patch("app.modules.deals.repository.DealRepository.get_by_id", new_callable=AsyncMock)
    async def test_update_deal_with_stage_in_body_returns_422_invalid_stage_transition(
        self, mock_get
    ):
        mock_get.return_value = _fake_deal(self._deal_id, self._tenant_id)
        app = self._override_current_user()
        try:
            resp = await self.client.patch(
                f"/api/v1/deals/{self._deal_id}", json={"stage": "won"}
            )
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)
        self.assertEqual(resp.json()["error"]["code"], "INVALID_STAGE_TRANSITION")

    @patch("app.modules.deals.repository.DealRepository.get_by_id", new_callable=AsyncMock)
    async def test_update_deal_with_status_won_returns_422_invalid_stage_transition(
        self, mock_get
    ):
        mock_get.return_value = _fake_deal(self._deal_id, self._tenant_id)
        app = self._override_current_user()
        try:
            resp = await self.client.patch(
                f"/api/v1/deals/{self._deal_id}", json={"status": "won"}
            )
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)
        self.assertEqual(resp.json()["error"]["code"], "INVALID_STAGE_TRANSITION")

    @patch("app.modules.deals.repository.DealRepository.update", new_callable=AsyncMock)
    @patch("app.modules.deals.repository.DealRepository.get_by_id", new_callable=AsyncMock)
    async def test_update_deal_recomputes_weighted_value(self, mock_get, mock_update):
        mock_get.return_value = _fake_deal(
            self._deal_id, self._tenant_id, value=Decimal("100"), probability=50,
        )
        mock_update.return_value = _fake_deal(self._deal_id, self._tenant_id)
        app = self._override_current_user()
        try:
            resp = await self.client.patch(
                f"/api/v1/deals/{self._deal_id}", json={"probability": 80}
            )
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 200)
        call_data = mock_update.call_args.args[1]
        self.assertEqual(call_data["weighted_value"], Decimal("80.00"))

    @patch("app.modules.deals.repository.DealRepository.update", new_callable=AsyncMock)
    @patch("app.modules.deals.repository.DealRepository.get_by_id", new_callable=AsyncMock)
    async def test_update_deal_unlink_contact_id(self, mock_get, mock_update):
        mock_get.return_value = _fake_deal(
            self._deal_id, self._tenant_id, contact_id=uuid.uuid4(),
        )
        mock_update.return_value = _fake_deal(self._deal_id, self._tenant_id)
        app = self._override_current_user()
        try:
            resp = await self.client.patch(
                f"/api/v1/deals/{self._deal_id}", json={"contact_id": None}
            )
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 200)
        call_data = mock_update.call_args.args[1]
        self.assertIsNone(call_data["contact_id"])

    # ── abandon / reopen (generic PATCH status) ─────────────────────────────────

    @patch("app.modules.deals.repository.DealRepository.update", new_callable=AsyncMock)
    @patch("app.modules.deals.repository.DealRepository.get_by_id", new_callable=AsyncMock)
    async def test_update_deal_open_to_abandoned_succeeds(self, mock_get, mock_update):
        mock_get.return_value = _fake_deal(self._deal_id, self._tenant_id, status="open")
        mock_update.return_value = _fake_deal(
            self._deal_id, self._tenant_id, status="abandoned"
        )
        app = self._override_current_user()
        try:
            resp = await self.client.patch(
                f"/api/v1/deals/{self._deal_id}", json={"status": "abandoned"}
            )
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "abandoned")

    @patch("app.modules.deals.repository.DealRepository.update", new_callable=AsyncMock)
    @patch("app.modules.deals.repository.DealRepository.get_by_id", new_callable=AsyncMock)
    async def test_update_deal_abandoned_to_open_succeeds(self, mock_get, mock_update):
        mock_get.return_value = _fake_deal(self._deal_id, self._tenant_id, status="abandoned")
        mock_update.return_value = _fake_deal(self._deal_id, self._tenant_id, status="open")
        app = self._override_current_user()
        try:
            resp = await self.client.patch(
                f"/api/v1/deals/{self._deal_id}", json={"status": "open"}
            )
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "open")

    @patch("app.modules.deals.repository.DealRepository.get_by_id", new_callable=AsyncMock)
    async def test_update_deal_status_from_won_returns_422(self, mock_get):
        mock_get.return_value = _fake_deal(self._deal_id, self._tenant_id, status="won")
        app = self._override_current_user()
        try:
            resp = await self.client.patch(
                f"/api/v1/deals/{self._deal_id}", json={"status": "abandoned"}
            )
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)
        self.assertEqual(resp.json()["error"]["code"], "INVALID_STAGE_TRANSITION")

    # ── delete ────────────────────────────────────────────────────────────────

    @patch("app.modules.deals.repository.DealRepository.delete", new_callable=AsyncMock)
    @patch("app.modules.deals.repository.DealRepository.get_by_id", new_callable=AsyncMock)
    async def test_delete_deal_success(self, mock_get, mock_delete):
        mock_get.return_value = _fake_deal(self._deal_id, self._tenant_id)
        app = self._override_current_user()
        try:
            resp = await self.client.delete(f"/api/v1/deals/{self._deal_id}")
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"message": "Deal deleted successfully."})
        mock_delete.assert_called_once()

    @patch("app.modules.deals.repository.DealRepository.get_by_id", new_callable=AsyncMock)
    async def test_delete_deal_not_found_returns_404(self, mock_get):
        mock_get.return_value = None
        app = self._override_current_user()
        try:
            resp = await self.client.delete(f"/api/v1/deals/{self._deal_id}")
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 404)
