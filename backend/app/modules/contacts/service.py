from app.modules.contacts.repository import ContactRepository


class ContactService:
    """Internal domain logic for contacts. Never imported from outside this module."""

    def __init__(self, repo: ContactRepository) -> None:
        self._repo = repo

    # Placeholder — implement contact domain logic here.
