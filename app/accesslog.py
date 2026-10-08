"""Middleware ASGI de log de acceso en formato tipo nginx para Fail2Ban.

Escribe una línea por petición en el archivo configurado (montado desde el
host). Usa la cabecera X-Real-IP que pone el proxy nginx del frontend cuando
la hay; si la petición llega directa, usa la IP real del cliente.

Formato (estilo nginx common + tiempo de respuesta):
    <ip> - - [fecha/hora +0000] "METHOD path HTTP/1.1" <status> <ms>
"""

import logging
import time
from typing import Any

from starlette.types import ASGIApp, Receive, Scope, Send

DEFAULT_ACCESS_LOG = "/var/log/app/access.log"

access_logger = logging.getLogger("accesslog")


def configure_access_logger(path: str = DEFAULT_ACCESS_LOG) -> None:
    """Configura el logger con un FileHandler que escribe 'una línea = una petición'."""
    access_logger.setLevel(logging.INFO)
    if access_logger.handlers:
        return
    handler = logging.FileHandler(path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(message)s"))
    access_logger.addHandler(handler)
    access_logger.propagate = False


def _client_ip(scope: Scope) -> str:
    client = scope.get("client")
    return client[0] if client else "-"


def _real_ip(scope: Scope) -> str:
    for name, value in scope.get("headers", []):
        if name.lower() == b"x-real-ip":
            return value.decode("latin1")
    return _client_ip(scope)


class AccessLogMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start = time.perf_counter()
        status: dict[str, Any] = {}

        async def send_wrapper(message: dict[str, Any]) -> None:
            if message["type"] == "http.response.start":
                status["status"] = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            status["status"] = 500
            raise
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            access_logger.info(
                '%s - - [%s] "%s %s HTTP/1.1" %s %.1f',
                _real_ip(scope),
                time.strftime("%d/%b/%Y:%H:%M:%S %z"),
                scope.get("method", "-"),
                scope.get("path", "-"),
                status.get("status", "-"),
                elapsed_ms,
            )