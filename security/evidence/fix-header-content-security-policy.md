# Evidencia — cabecera Content-Security-Policy (jwt-ldap-auth)

Hallazgo de Nuclei: `http-missing-security-headers` (falta `Content-Security-Policy`).

## Antes

Las respuestas del servicio no incluían la cabecera `Content-Security-Policy`.

## Corrección

Se añade a `SECURITY_HEADERS` en `app/security_headers.py`:

```python
b"content-security-policy": b"default-src 'none'; frame-ancestors 'none'",
```

## Validación

```console
$ RUN_INTEGRATION=1 pytest -o addopts="" -q tests/test_security_headers.py
3 passed
$ curl -sI http://localhost:8000/health | grep -i '^content-security-policy:'
content-security-policy: default-src 'none'; frame-ancestors 'none'
```

La prueba unitaria recorre `SECURITY_HEADERS`, así que exige esta cabecera en
cada respuesta; la de integración la comprueba contra `/health`.
