"""Valida la corrección del hallazgo de Nuclei `swagger-api`.
Con `DOCS_ENABLED=0` (por defecto) la Swagger UI no debe existir: /docs responde 404.

Requiere el stack levantado:

    RUN_INTEGRATION=1 pytest -q tests/test_docs_disabled.py
"""

import os

import pytest

RUN_INTEGRATION = os.getenv("RUN_INTEGRATION") == "1"
AUTH_URL = os.getenv("AUTH_URL", "http://localhost:8000")


@pytest.mark.skipif(
    not RUN_INTEGRATION, reason="requiere RUN_INTEGRATION=1 y el stack levantado"
)
@pytest.mark.parametrize("path", ["/docs"])
def test_documentacion_no_accesible(path):
    import httpx

    response = httpx.get(f"{AUTH_URL}{path}", timeout=10)
    assert response.status_code == 404, f"{path} sigue expuesto (HTTP {response.status_code})"
