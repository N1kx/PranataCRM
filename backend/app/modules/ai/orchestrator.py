from app.modules.ai.agents.deal_scorer import DealScorerAgent
from app.modules.ai.agents.followup_agent import FollowUpAgent
from app.modules.ai.agents.rag_chatbot import RAGChatbot
from app.modules.ai.agents.summarizer import SummarizerAgent


class AIOrchestrator:
    """Coordinates AI agents for complex multi-step workflows."""

    def __init__(
        self,
        deal_scorer: DealScorerAgent,
        followup: FollowUpAgent,
        summarizer: SummarizerAgent,
        chatbot: RAGChatbot,
    ) -> None:
        self.deal_scorer = deal_scorer
        self.followup = followup
        self.summarizer = summarizer
        self.chatbot = chatbot
