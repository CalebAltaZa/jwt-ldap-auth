"""Middleware ASGI que añade cabeceras de seguridad a todas las respuestas.

Hallazgo de Nuclei: faltan cabeceras de endurecimiento en las respuestas HTTP.
Se aplican a nivel de aplicación para que también cubran peticiones que no pasan
por el reverse-proxy nginx.
"""

from starlette.types import ASGIApp, Receive, Scope, Send

# Cabeceras de endurecimiento. Para una API JSON la CSP puede ser restrictiva.
SECURITY_HEADERS: dict[bytes, bytes] = {
    b"x-content-type-options": b"nosniff",
    b"x-frame-options": b"DENY",
    b"referrer-policy": b"no-referrer",
    b"x-permitted-cross-domain-policies": b"none",
    b"cross-origin-opener-policy": b"same-origin",
    b"cross-origin-embedder-policy": b"require-corp",
    b"cross-origin-resource-policy": b"same-origin",
    b"permissions-policy": b"geolocation=(), microphone=(), camera=()",
    b"content-security-policy": b"default-src 'none'; frame-ancestors 'none'",
    b"strict-transport-security": b"max-age=31536000; includeSubDomains",
}


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message: dict) -> None:
            if message["type"] == "http.response.start":
                headers = message.setdefault("headers", [])
                present = {name.lower() for name, _ in headers}
                for name, value in SECURITY_HEADERS.items():
                    if name not in present:
                        headers.append((name, value))
            await send(message)

        await self.app(scope, receive, send_wrapper)
