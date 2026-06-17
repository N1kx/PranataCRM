from app.modules.deals.repository import DealRepository


class DealService:
    """Internal domain logic for deals. Never imported from outside this module."""

    def __init__(self, repo: DealRepository) -> None:
        self._repo = repo

    # Placeholder — implement deal domain logic here.
    # Access contact info via ContactContractProtocol injected into DealUseCase, not here.
