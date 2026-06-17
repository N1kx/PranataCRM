from uuid import UUID

from app.modules.ai.service import AIService
from app.shared.contracts.ai_contract import DealScoreDTO


class DealScorerAgent:
    def __init__(self, ai_service: AIService) -> None:
        self._ai = ai_service

    async def score(self, deal_id: UUID, context: str) -> DealScoreDTO:
        # Placeholder — build prompt and parse LLM output.
        raise NotImplementedError
