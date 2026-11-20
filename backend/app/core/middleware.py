from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.config import Settings
from app.core.logging import new_request_id, request_id_ctx


class RequestContextMiddleware:
    def __init__(self, app: ASGIApp, settings: Settings) -> None:
        self.app = app
        self.settings = settings

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = {k.decode("latin-1"): v.decode("latin-1") for k, v in scope.get("headers", [])}
        incoming = headers.get("x-request-id")
        request_id = incoming if incoming else new_request_id()
        token = request_id_ctx.set(request_id)

        async def send_with_headers(message: dict) -> None:
            if message["type"] == "http.response.start":
                extra = [
                    (b"x-request-id", request_id.encode("latin-1")),
                    (b"x-content-type-options", b"nosniff"),
                    (b"x-frame-options", b"DENY"),
                    (b"referrer-policy", b"strict-origin-when-cross-origin"),
                    (b"cache-control", b"no-store"),
                ]
                if self.settings.is_production:
                    extra.append(
                        (b"strict-transport-security", b"max-age=31536000; includeSubDomains")
                    )
                message = {
                    **message,
                    "headers": list(message.get("headers", [])) + extra,
                }
            await send(message)

        try:
            await self.app(scope, receive, send_with_headers)
        finally:
            request_id_ctx.reset(token)


def register_middleware(app: FastAPI, settings: Settings) -> None:
    app.add_middleware(RequestContextMiddleware, settings=settings)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "X-Organization-Id",
            "X-Branch-Id",
            "Idempotency-Key",
            "X-CSRF-Token",
        ],
    )
    if settings.is_production:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
