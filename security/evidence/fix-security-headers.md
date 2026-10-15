# Evidencia — Cabeceras de seguridad (jwt-ldap-auth)

Hallazgo de Nuclei: `http-missing-security-headers` (×10).

## Antes

Las respuestas de la API (`uvicorn`) no incluían cabeceras de endurecimiento.

## Corrección

`app/security_headers.py` implementa `SecurityHeadersMiddleware`, registrado en
`app/main.py`. Añade 10 cabeceras a todas las respuestas (respetando las que ya
vengan puestas).

## Después (servicio reconstruido)

```console
$ curl -s -D - -o /dev/null http://localhost:8000/health
HTTP/1.1 200 OK
server: uvicorn
x-content-type-options: nosniff
x-frame-options: DENY
referrer-policy: no-referrer
x-permitted-cross-domain-policies: none
cross-origin-opener-policy: same-origin
cross-origin-embedder-policy: require-corp
cross-origin-resource-policy: same-origin
permissions-policy: geolocation=(), microphone=(), camera=()
content-security-policy: default-src 'none'; frame-ancestors 'none'
strict-transport-security: max-age=31536000; includeSubDomains
```

## Validación automatizada

```console
$ pytest -q tests/test_security_headers.py            # unitaria
2 passed, 4 skipped in 0.04s
$ RUN_INTEGRATION=1 pytest -q tests/test_security_headers.py   # + integración
6 passed in 0.26s
```

- Unitaria: el middleware añade las 10 cabeceras y no pisa las existentes.
- Integración: `/health` real devuelve cada cabecera con su valor.
