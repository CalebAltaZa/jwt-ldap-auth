# Evidencia — cabecera Cross-Origin-Resource-Policy (jwt-ldap-auth)

Hallazgo de Nuclei: `http-missing-security-headers` (falta `Cross-Origin-Resource-Policy`).

## Antes

Las respuestas del servicio no incluían la cabecera `Cross-Origin-Resource-Policy`.

## Corrección

Se añade a `SECURITY_HEADERS` en `app/security_headers.py`:

```python
b"cross-origin-resource-policy": b"same-origin",
```

## Validación

```console
$ RUN_INTEGRATION=1 pytest -o addopts="" -q tests/test_security_headers.py
3 passed
$ curl -sI http://localhost:8000/health | grep -i '^cross-origin-resource-policy:'
cross-origin-resource-policy: same-origin
```

La prueba unitaria recorre `SECURITY_HEADERS`, así que exige esta cabecera en
cada respuesta; la de integración la comprueba contra `/health`.
