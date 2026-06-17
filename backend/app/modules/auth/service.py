from app.modules.auth.repository import AuthRepository


class AuthService:
    """Internal domain logic for auth. Never imported from outside this module."""

    def __init__(self, repo: AuthRepository) -> None:
        self._repo = repo

    # Placeholder — implement password hashing, token generation, etc.
