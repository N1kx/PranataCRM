import uuid

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.shared.logging import request_id_ctx, user_id_ctx


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

        # Also stash on scope["state"] (-> request.state): Starlette dispatches the
        # base Exception handler from ServerErrorMiddleware, which sits *outside*
        # this middleware, so by the time it runs, the finally-block below has
        # already reset these ContextVars. request.state survives that boundary.
        scope.setdefault("state", {})["request_id"] = request_id

        request_id_token = request_id_ctx.set(request_id)
        user_id_token = user_id_ctx.set(None)

        async def send_with_request_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                message.setdefault("headers", [])
                message["headers"].append(
                    (b"x-request-id", request_id.encode("latin-1"))
                )
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        finally:
            request_id_ctx.reset(request_id_token)
            user_id_ctx.reset(user_id_token)
