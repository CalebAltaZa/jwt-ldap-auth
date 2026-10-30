# Evidencia — cabecera Referrer-Policy (jwt-ldap-auth)

Hallazgo de Nuclei: `http-missing-security-headers` (falta `Referrer-Policy`).

## Antes

Las respuestas del servicio no incluían la cabecera `Referrer-Policy`.

## Corrección

Se añade a `SECURITY_HEADERS` en `app/security_headers.py`:

```python
b"referrer-policy": b"no-referrer",
```

## Validación

```console
$ RUN_INTEGRATION=1 pytest -o addopts="" -q tests/test_security_headers.py
3 passed
$ curl -sI http://localhost:8000/health | grep -i '^referrer-policy:'
referrer-policy: no-referrer
```

La prueba unitaria recorre `SECURITY_HEADERS`, así que exige esta cabecera en
cada respuesta; la de integración la comprueba contra `/health`.
