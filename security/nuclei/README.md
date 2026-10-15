# Análisis de seguridad con Nuclei — LDAP / Auth (jwt-ldap-auth)

Análisis de vulnerabilidades del **servicio de autenticación** (FastAPI que
valida credenciales contra OpenLDAP y firma el JWT) y del **puerto TLS de
LDAP**, usando **Nuclei** de ProjectDiscovery dentro de un contenedor Docker.

- **Fecha del análisis:** 2026-10-14
- **Objetivos escaneados:**
  - `http://jwt-auth:8000` (contenedor `jwt-auth`) → [`nuclei-auth.jsonl`](nuclei-auth.jsonl)
  - `ldap.example.com:636` (contenedor `jwt-openldap`, LDAPS) → [`nuclei-ldap.jsonl`](nuclei-ldap.jsonl)
- **Imagen:** `projectdiscovery/nuclei:latest` (nuclei v3.11.1)
- **Plantillas:** `nuclei-templates v10.5.0` (11.154 plantillas)

## Cómo se ejecutó

Nuclei se conectó a la **red del stack** (`practicajwt_app-net`) para alcanzar
tanto la API de auth por nombre (`jwt-auth:8000`) como el puerto LDAPS del
contenedor de OpenLDAP (`ldap.example.com:636`):

```bash
# API de autenticación
docker run --rm --network practicajwt_app-net \
  -v nuclei-templates:/root/nuclei-templates \
  -v "$PWD/security/nuclei:/reports" \
  projectdiscovery/nuclei:latest \
  -target http://jwt-auth:8000 \
  -severity info,low,medium,high,critical \
  -jsonl-export /reports/nuclei-auth.jsonl -stats -no-color

# Puerto LDAPS (plantillas de red/TLS)
docker run --rm --network practicajwt_app-net \
  -v nuclei-templates:/root/nuclei-templates \
  -v "$PWD/security/nuclei:/reports" \
  projectdiscovery/nuclei:latest \
  -target ldap.example.com:636 -t ssl/ -t network/ \
  -severity info,low,medium,high,critical \
  -jsonl-export /reports/nuclei-ldap.jsonl -no-color
```

## Hallazgos

### API de autenticación `http://jwt-auth:8000` (15)

| Severidad | Plantilla | Hallazgo |
|---|---|---|
| info | `swagger-api` | Swagger UI público (`/docs`) |
| info | `redoc-api-docs` | ReDoc (`/redoc`) |
| info | `openapi` | Especificación OpenAPI expuesta |
| info | `soa-detect` | Registro SOA/DNS detectado |
| info | `tech-detect` | Fingerprinting de tecnología |
| info | `http-missing-security-headers` (×10) | Faltan cabeceras de seguridad |

Cabeceras ausentes: `Strict-Transport-Security`, `Content-Security-Policy`,
`X-Frame-Options`, `X-Content-Type-Options`, `X-Permitted-Cross-Domain-Policies`,
`Referrer-Policy`, `Cross-Origin-Opener-Policy`, `Permissions-Policy`,
`Cross-Origin-Embedder-Policy`, `Cross-Origin-Resource-Policy`.

### Puerto LDAPS `ldap.example.com:636` (3)

| Severidad | Plantilla | Hallazgo |
|---|---|---|
| info | `tls-version` | TLS 1.2 negociado (`tls12`) |
| info | `ssl-dns-names` | Nombres en el certificado: `ldap.example.com`, `openldap` |
| **low** | `untrusted-root-certificate` | **Certificado raíz no confiable** (CA propia) |

## Interpretación

1. **Certificado raíz no confiable (low).** LDAP usa una **CA propia** generada
   por `setup.sh`; un cliente que no confíe en esa CA no valida la cadena. Dentro
   del stack es intencional (el servicio `auth` verifica con
   `Tls(validate=CERT_REQUIRED, ca_certs_file=...)`), pero fuera del entorno el
   certificado es "desconocido". Riesgo aceptado y documentado.
2. **Solo TLS 1.2.** Se recomienda fijar TLS 1.3 (o TLS 1.2 + suites seguras) en
   la configuración de OpenLDAP.
3. **Documentación de API expuesta** (Swagger/ReDoc/OpenAPI): misma observación
   que en el backend de items.
4. **Cabeceras de seguridad ausentes**: se corrigen en el servicio o en el
   reverse-proxy nginx.

## Estado

Correcciones aplicadas en este repositorio, **cada una con su prueba**:

- [x] Deshabilitar/proteger `/docs`, `/redoc` y `/openapi.json` por defecto
      (`DOCS_ENABLED=1` para habilitarlos en desarrollo).
      Validado por [`tests/test_docs_disabled.py`](../../tests/test_docs_disabled.py)
      y [`security/evidence/fix-docs-disabled.md`](../evidence/fix-docs-disabled.md).
- [x] Middleware de cabeceras de seguridad (`security_headers.py`).
      Validado por [`tests/test_security_headers.py`](../../tests/test_security_headers.py)
      y [`security/evidence/fix-security-headers.md`](../evidence/fix-security-headers.md).

Hallazgos de LDAP evaluados y **aceptados como riesgo** (no aplican a este repo):

- [x] **`untrusted-root-certificate` (low):** es la **CA propia** del laboratorio
      (generada por `setup.sh`). El cliente `auth` sí confía en ella
      (`Tls(validate=CERT_REQUIRED, ca_certs_file=/secrets/ldap_ca.crt)`); fuera
      del entorno aparece como "desconocida". No es explotable en este contexto.
- [x] **`tls-version` (info, TLS 1.2):** TLS 1.2 sigue siendo seguro y
      recomendado. Forzar TLS 1.3 requiere configuración **del servidor slapd**
      (`olcTLSProtocolMin: 0x0304` en OpenLDAP), que vive en el `docker-compose.yml`
      del proyecto (fuera de este repositorio). Se documenta como mejora opcional.

> Tras las correcciones hay que reconstruir la imagen
> (`docker compose build auth && docker compose up -d auth`) y volver a lanzar
> Nuclei para confirmar que los hallazgos desaparecen.
