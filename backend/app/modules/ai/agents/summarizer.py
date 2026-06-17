from uuid import UUID

from app.modules.ai.service import AIService
from app.shared.contracts.ai_contract import AISummaryDTO


class SummarizerAgent:
    def __init__(self, ai_service: AIService) -> None:
        self._ai = ai_service

    async def summarize(self, subject_id: UUID, text: str) -> AISummaryDTO:
        # Placeholder — summarize contact/deal notes.
        raise NotImplementedError
