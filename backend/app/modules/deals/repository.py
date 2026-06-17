from sqlalchemy.ext.asyncio import AsyncSession


class DealRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # Placeholder — implement CRUD for Deal model here.
