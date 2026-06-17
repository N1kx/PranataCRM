"""
Dependency wiring — the ONLY place where concrete classes are bound to Protocols.
No business logic lives here.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai.agents.deal_scorer import DealScorerAgent
from app.modules.ai.agents.followup_agent import FollowUpAgent
from app.modules.ai.agents.rag_chatbot import RAGChatbot
from app.modules.ai.agents.summarizer import SummarizerAgent
from app.modules.ai.orchestrator import AIOrchestrator
from app.modules.ai.service import AIService
from app.modules.ai.use_case import AIUseCase
from app.modules.auth.repository import AuthRepository
from app.modules.auth.service import AuthService
from app.modules.auth.use_case import AuthUseCase
from app.modules.billing.service import BillingService
from app.modules.billing.use_case import BillingUseCase
from app.modules.contacts.repository import ContactRepository
from app.modules.contacts.service import ContactService
from app.modules.contacts.use_case import ContactUseCase
from app.modules.deals.repository import DealRepository
from app.modules.deals.service import DealService
from app.modules.deals.use_case import DealUseCase
from app.modules.notifications.service import NotificationService
from app.modules.notifications.use_case import NotificationUseCase


class Container:
    """
    Builds and holds fully-wired use-case instances.
    Session is injected per-request via FastAPI Depends in production;
    this class wires the module graph that does not depend on a live session.
    """

    def __init__(self, session: AsyncSession | None = None) -> None:
        self._session = session
        self._build()

    def _build(self) -> None:
        session = self._session  # may be None during startup before first request

        # ── AI (no DB) ────────────────────────────────────────────────────────
        _ai_service = AIService()
        _orchestrator = AIOrchestrator(
            deal_scorer=DealScorerAgent(_ai_service),
            followup=FollowUpAgent(_ai_service),
            summarizer=SummarizerAgent(_ai_service),
            chatbot=RAGChatbot(_ai_service),
        )
        self.ai_use_case = AIUseCase(_orchestrator)

        # ── Notifications (no DB) ─────────────────────────────────────────────
        _notification_service = NotificationService()
        self.notification_use_case = NotificationUseCase(_notification_service)

        # ── Billing (no DB) ───────────────────────────────────────────────────
        _billing_service = BillingService()
        self.billing_use_case = BillingUseCase(_billing_service)

        # ── Auth ──────────────────────────────────────────────────────────────
        _auth_repo = AuthRepository(session)  # type: ignore[arg-type]
        _auth_service = AuthService(_auth_repo)
        self.auth_use_case = AuthUseCase(_auth_service)

        # ── Contacts ──────────────────────────────────────────────────────────
        _contact_repo = ContactRepository(session)  # type: ignore[arg-type]
        _contact_service = ContactService(_contact_repo)
        self.contact_use_case = ContactUseCase(_contact_service)

        # ── Deals ─────────────────────────────────────────────────────────────
        # Once DealContractProtocol and ContactContractProtocol are defined,
        # wire contacts=self.contact_use_case here.
        _deal_repo = DealRepository(session)  # type: ignore[arg-type]
        _deal_service = DealService(_deal_repo)
        self.deal_use_case = DealUseCase(_deal_service)


# Module-level singleton used by routers via lazy import.
# Per-request session injection is handled via FastAPI Depends in each router.
container = Container()
