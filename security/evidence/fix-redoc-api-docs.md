# Evidencia — ReDoc deshabilitado (jwt-ldap-auth)

Hallazgo de Nuclei: `redoc-api-docs` (`/redoc`).

## Antes

`/redoc` respondía **HTTP 200** (documentación/esquema expuestos).

## Corrección

`redoc_url=None` cuando `DOCS_ENABLED=0` (`app/config.py` + `app/main.py`).

## Después (servicio reconstruido)

```console
$ curl -s -o /dev/null -w '%{http_code}\n' http://localhost:8000/redoc
404
```

## Validación automatizada

```console
$ RUN_INTEGRATION=1 pytest -q tests/test_docs_disabled.py
2 passed
```

(La prueba exige `404` en /docs y /redoc.)
