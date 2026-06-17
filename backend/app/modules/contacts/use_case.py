from app.modules.contacts.service import ContactService

# ContactUseCase will implement ContactContractProtocol once it is defined in
# shared/contracts/contact_contract.py. Method signatures must match the contract exactly.


class ContactUseCase:
    """Entry point for the contacts module. Will implement ContactContractProtocol."""

    def __init__(self, service: ContactService) -> None:
        self._service = service
