from sqlalchemy.ext.asyncio import AsyncSession


class ContactRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # Placeholder — implement CRUD for Contact model here.
