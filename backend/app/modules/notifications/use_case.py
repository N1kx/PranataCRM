from app.modules.notifications.service import NotificationService

# NotificationUseCase will implement NotificationContractProtocol once it is defined in
# shared/contracts/notification_contract.py. Method signatures must match the contract exactly.


class NotificationUseCase:
    """Entry point for the notifications module. Will implement NotificationContractProtocol."""

    def __init__(self, service: NotificationService) -> None:
        self._service = service
