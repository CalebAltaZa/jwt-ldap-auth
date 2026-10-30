# Evidencia — Swagger UI deshabilitada (jwt-ldap-auth)

Hallazgo de Nuclei: `swagger-api` (`/docs`).

## Antes

`/docs` respondía **HTTP 200** (documentación/esquema expuestos).

## Corrección

`docs_url=None` cuando `DOCS_ENABLED=0` (`app/config.py` + `app/main.py`).

## Después (servicio reconstruido)

```console
$ curl -s -o /dev/null -w '%{http_code}\n' http://localhost:8000/docs
404
```

## Validación automatizada

```console
$ RUN_INTEGRATION=1 pytest -q tests/test_docs_disabled.py
1 passed
```

(La prueba exige `404` en /docs.)
