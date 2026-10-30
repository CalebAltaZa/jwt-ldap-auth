# Evidencia — cabecera Strict-Transport-Security (jwt-ldap-auth)

Hallazgo de Nuclei: `http-missing-security-headers` (falta `Strict-Transport-Security`).

## Antes

Las respuestas del servicio no incluían la cabecera `Strict-Transport-Security`.

## Corrección

Se añade a `SECURITY_HEADERS` en `app/security_headers.py`:

```python
b"strict-transport-security": b"max-age=31536000; includeSubDomains",
```

## Validación

```console
$ RUN_INTEGRATION=1 pytest -o addopts="" -q tests/test_security_headers.py
3 passed
$ curl -sI http://localhost:8000/health | grep -i '^strict-transport-security:'
strict-transport-security: max-age=31536000; includeSubDomains
```

La prueba unitaria recorre `SECURITY_HEADERS`, así que exige esta cabecera en
cada respuesta; la de integración la comprueba contra `/health`.
