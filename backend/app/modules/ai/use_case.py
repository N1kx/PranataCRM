from app.modules.ai.orchestrator import AIOrchestrator

# AIUseCase will implement AIContractProtocol once it is defined in
# shared/contracts/ai_contract.py. Method signatures must match the contract exactly.


class AIUseCase:
    """Entry point for the AI module. Will implement AIContractProtocol."""

    def __init__(self, orchestrator: AIOrchestrator) -> None:
        self._orchestrator = orchestrator
