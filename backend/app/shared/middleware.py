import uuid

import structlog
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class RequestIDMiddleware:
    """Pure ASGI middleware — guarantees contextvars propagate to the route handler."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers") or [])
        incoming = headers.get(b"x-request-id")
        request_id = incoming.decode("latin-1") if incoming else str(uuid.uuid4())

        # Also stash on scope["state"] (-> request.state): the handler for
        # unhandled exceptions runs at ServerErrorMiddleware level, *outside*
        # this middleware, and reads the id from there.
        scope.setdefault("state", {})["request_id"] = request_id

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        async def send_with_request_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                response_headers = message.setdefault("headers", [])
                # The exception handlers set this header on their own responses;
                # only add it when it is not already present.
                if not any(name.lower() == b"x-request-id" for name, _ in response_headers):
                    response_headers.append(
                        (b"x-request-id", request_id.encode("latin-1"))
                    )
            await send(message)

        await self.app(scope, receive, send_with_request_id)
