from app.modules.billing.service import BillingService

# BillingUseCase will implement BillingContractProtocol once it is defined in
# shared/contracts/billing_contract.py. Method signatures must match the contract exactly.


class BillingUseCase:
    """Entry point for the billing module. Will implement BillingContractProtocol."""

    def __init__(self, service: BillingService) -> None:
        self._service = service
