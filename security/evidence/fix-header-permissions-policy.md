# Evidencia — cabecera Permissions-Policy (jwt-ldap-auth)

Hallazgo de Nuclei: `http-missing-security-headers` (falta `Permissions-Policy`).

## Antes

Las respuestas del servicio no incluían la cabecera `Permissions-Policy`.

## Corrección

Se añade a `SECURITY_HEADERS` en `app/security_headers.py`:

```python
b"permissions-policy": b"geolocation=(), microphone=(), camera=()",
```

## Validación

```console
$ RUN_INTEGRATION=1 pytest -o addopts="" -q tests/test_security_headers.py
3 passed
$ curl -sI http://localhost:8000/health | grep -i '^permissions-policy:'
permissions-policy: geolocation=(), microphone=(), camera=()
```

La prueba unitaria recorre `SECURITY_HEADERS`, así que exige esta cabecera en
cada respuesta; la de integración la comprueba contra `/health`.
