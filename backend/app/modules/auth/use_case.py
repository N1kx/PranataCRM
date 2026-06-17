from app.modules.auth.service import AuthService
from app.modules.auth.schemas import LoginRequest, TokenResponse, RegisterRequest


class AuthUseCase:
    """Entry point for the auth module. Orchestrates AuthService."""

    def __init__(self, service: AuthService) -> None:
        self._service = service

    async def login(self, request: LoginRequest) -> TokenResponse:
        # Placeholder
        raise NotImplementedError

    async def register(self, request: RegisterRequest) -> TokenResponse:
        # Placeholder
        raise NotImplementedError

    async def refresh(self, refresh_token: str) -> TokenResponse:
        # Placeholder
        raise NotImplementedError

    async def logout(self, access_token: str) -> None:
        # Placeholder
        raise NotImplementedError
