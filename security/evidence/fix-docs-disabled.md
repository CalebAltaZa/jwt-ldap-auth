# Evidencia — Swagger / ReDoc / OpenAPI deshabilitados (jwt-ldap-auth)

Hallazgo de Nuclei: `swagger-api`, `redoc-api-docs` y `openapi`.

## Antes

`/docs`, `/redoc` y `/openapi.json` respondían **HTTP 200** (Swagger UI y
esquema OpenAPI públicos; ver `nuclei-auth.jsonl`).

## Corrección

`docs_url`, `redoc_url` y `openapi_url` sólo se montan si `DOCS_ENABLED=1`
(`app/config.py` y `app/main.py`). Por defecto (`DOCS_ENABLED=0`) no existen.

## Después (servicio reconstruido)

```console
$ for p in /docs /redoc /openapi.json; do
    printf "%-14s -> " "$p"
    curl -s -o /dev/null -w '%{http_code}\n' "http://localhost:8000$p"
  done
/docs          -> 404
/redoc         -> 404
/openapi.json  -> 404
```

## Validación automatizada

```console
$ RUN_INTEGRATION=1 pytest -q tests/test_docs_disabled.py
6 passed in 0.26s
```

(La prueba parametriza los tres caminos y exige `404`.)
