from uuid import UUID

from app.modules.ai.service import AIService


class FollowUpAgent:
    def __init__(self, ai_service: AIService) -> None:
        self._ai = ai_service

    async def suggest_followup(self, contact_id: UUID, history: str) -> str:
        # Placeholder — generate follow-up message suggestion.
        raise NotImplementedError
