"""Valida la corrección del hallazgo de Nuclei `http-missing-security-headers`.

* Prueba unitaria (siempre): el middleware añade TODAS las cabeceras a
  cualquier respuesta ASGI y respeta las que ya vienen puestas.
* Prueba de integración (RUN_INTEGRATION=1): el servicio real devuelve las
  cabeceras en /health.

    pytest -q                              # unitarias
    RUN_INTEGRATION=1 pytest -q            # + integración
"""

import asyncio
import os

import pytest

from app.security_headers import SECURITY_HEADERS, SecurityHeadersMiddleware

RUN_INTEGRATION = os.getenv("RUN_INTEGRATION") == "1"
AUTH_URL = os.getenv("AUTH_URL", "http://localhost:8000")


def _run_asgi(app, scope):
    messages = []

    async def receive():
        return {"type": "http.request"}

    async def send(message):
        messages.append(message)

    asyncio.run(app(scope, receive, send))
    return messages


def test_middleware_anade_todas_las_cabeceras():
    async def dummy_app(scope, receive, send):
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})

    messages = _run_asgi(SecurityHeadersMiddleware(dummy_app), {"type": "http"})
    headers = {name.lower(): value for name, value in messages[0]["headers"]}

    assert headers, "la respuesta no tiene cabeceras"
    for name, value in SECURITY_HEADERS.items():
        assert headers.get(name) == value, f"falta o difiere la cabecera {name!r}"


def test_middleware_no_pisa_cabeceras_existentes():
    async def dummy_app(scope, receive, send):
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [(b"x-frame-options", b"SAMEORIGIN")],
            }
        )
        await send({"type": "http.response.body", "body": b"ok"})

    messages = _run_asgi(SecurityHeadersMiddleware(dummy_app), {"type": "http"})
    headers = {name.lower(): value for name, value in messages[0]["headers"]}
    assert headers[b"x-frame-options"] == b"SAMEORIGIN"


@pytest.mark.skipif(
    not RUN_INTEGRATION, reason="requiere RUN_INTEGRATION=1 y el stack levantado"
)
def test_respuesta_real_incluye_cabeceras():
    import httpx

    response = httpx.get(f"{AUTH_URL}/health", timeout=10)
    for name, value in SECURITY_HEADERS.items():
        assert response.headers.get(name.decode()) == value.decode()
