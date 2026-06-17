from app.modules.ai.service import AIService


class RAGChatbot:
    def __init__(self, ai_service: AIService) -> None:
        self._ai = ai_service

    async def chat(self, session_id: str, message: str) -> str:
        # Placeholder — retrieve relevant docs from pgvector, then call LLM.
        raise NotImplementedError
