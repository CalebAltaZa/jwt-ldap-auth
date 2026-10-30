# Evidencia — cabecera X-Frame-Options (jwt-ldap-auth)

Hallazgo de Nuclei: `http-missing-security-headers` (falta `X-Frame-Options`).

## Antes

Las respuestas del servicio no incluían la cabecera `X-Frame-Options`.

## Corrección

Se añade a `SECURITY_HEADERS` en `app/security_headers.py`:

```python
b"x-frame-options": b"DENY",
```

## Validación

```console
$ RUN_INTEGRATION=1 pytest -o addopts="" -q tests/test_security_headers.py
3 passed
$ curl -sI http://localhost:8000/health | grep -i '^x-frame-options:'
x-frame-options: DENY
```

La prueba unitaria recorre `SECURITY_HEADERS`, así que exige esta cabecera en
cada respuesta; la de integración la comprueba contra `/health`.
