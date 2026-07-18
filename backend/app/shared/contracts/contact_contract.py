import uuid
from typing import Protocol

# ContactContractProtocol — the interface other modules use to check whether a
# contact_id reference is real, without importing the contacts module's
# internals. Concrete DTOs (e.g. a lightweight ContactDTO) can be added here
# once a cross-module need for more than existence checks arises.


class ContactContractProtocol(Protocol):
    async def contact_exists(
        self, tenant_id: uuid.UUID, contact_id: uuid.UUID
    ) -> bool: ...
