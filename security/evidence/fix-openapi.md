# Evidencia — Esquema OpenAPI deshabilitado (jwt-ldap-auth)

Hallazgo de Nuclei: `openapi` (`/openapi.json`).

## Antes

`/openapi.json` respondía **HTTP 200** (documentación/esquema expuestos).

## Corrección

`openapi_url=None` cuando `DOCS_ENABLED=0` (`app/config.py` + `app/main.py`).

## Después (servicio reconstruido)

```console
$ curl -s -o /dev/null -w '%{http_code}\n' http://localhost:8000/openapi.json
404
```

## Validación automatizada

```console
$ RUN_INTEGRATION=1 pytest -q tests/test_docs_disabled.py
3 passed
```

(La prueba exige `404` en /docs, /redoc y /openapi.json.)
