from app.config import get_settings

settings = get_settings()


class NotificationService:
    """Internal service for dispatching notifications. Never imported from outside this module."""

    async def send_email(self, to: str, subject: str, body: str) -> None:
        # Placeholder — integrate Resend or SMTP here.
        raise NotImplementedError

    async def send_in_app(self, user_id: str, subject: str, body: str) -> None:
        # Placeholder — persist and push in-app notification.
        raise NotImplementedError
