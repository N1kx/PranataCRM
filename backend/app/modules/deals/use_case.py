from app.modules.deals.service import DealService

# DealUseCase will implement DealContractProtocol once it is defined in
# shared/contracts/deal_contract.py. It will also receive ContactContractProtocol
# as a constructor argument — the ONLY way deals may access contact data.


class DealUseCase:
    """Entry point for the deals module. Will implement DealContractProtocol.
    Will access contacts ONLY via ContactContractProtocol — never via direct import."""

    def __init__(self, service: DealService) -> None:
        self._service = service
