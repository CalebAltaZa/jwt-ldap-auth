# Evidencia — cabecera X-Content-Type-Options (jwt-ldap-auth)

Hallazgo de Nuclei: `http-missing-security-headers` (falta `X-Content-Type-Options`).

## Antes

Las respuestas del servicio no incluían la cabecera `X-Content-Type-Options`.

## Corrección

Se añade a `SECURITY_HEADERS` en `app/security_headers.py`:

```python
b"x-content-type-options": b"nosniff",
```

## Validación

```console
$ RUN_INTEGRATION=1 pytest -o addopts="" -q tests/test_security_headers.py
3 passed
$ curl -sI http://localhost:8000/health | grep -i '^x-content-type-options:'
x-content-type-options: nosniff
```

La prueba unitaria recorre `SECURITY_HEADERS`, así que exige esta cabecera en
cada respuesta; la de integración la comprueba contra `/health`.
