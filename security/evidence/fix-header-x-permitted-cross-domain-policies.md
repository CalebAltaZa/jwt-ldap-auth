# Evidencia — cabecera X-Permitted-Cross-Domain-Policies (jwt-ldap-auth)

Hallazgo de Nuclei: `http-missing-security-headers` (falta `X-Permitted-Cross-Domain-Policies`).

## Antes

Las respuestas del servicio no incluían la cabecera `X-Permitted-Cross-Domain-Policies`.

## Corrección

Se añade a `SECURITY_HEADERS` en `app/security_headers.py`:

```python
b"x-permitted-cross-domain-policies": b"none",
```

## Validación

```console
$ RUN_INTEGRATION=1 pytest -o addopts="" -q tests/test_security_headers.py
3 passed
$ curl -sI http://localhost:8000/health | grep -i '^x-permitted-cross-domain-policies:'
x-permitted-cross-domain-policies: none
```

La prueba unitaria recorre `SECURITY_HEADERS`, así que exige esta cabecera en
cada respuesta; la de integración la comprueba contra `/health`.
