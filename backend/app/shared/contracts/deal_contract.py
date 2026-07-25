import uuid
from typing import Protocol

# DealContractProtocol — the interface other modules use to check whether a
# deal_id reference is real, without importing the deals module's internals.
# Concrete DTOs (e.g. a lightweight DealDTO) can be added here once a
# cross-module need for more than existence checks arises (e.g. activities).


class DealContractProtocol(Protocol):
    async def deal_exists(
        self, tenant_id: uuid.UUID, deal_id: uuid.UUID
    ) -> bool: ...
