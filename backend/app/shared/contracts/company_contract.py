import uuid
from typing import Protocol

# CompanyContractProtocol — the interface other modules use to check whether a
# company_id reference is real, without importing the companies module's
# internals. Concrete DTOs (e.g. a lightweight CompanyDTO) can be added here
# once a cross-module need for more than existence checks arises.


class CompanyContractProtocol(Protocol):
    async def company_exists(
        self, tenant_id: uuid.UUID, company_id: uuid.UUID
    ) -> bool: ...
