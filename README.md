# jwt-ldap-auth

Servicio de autenticacion: valida las credenciales del usuario contra **OpenLDAP**
y, si son correctas, emite un **JWT firmado con RS256** que las demas APIs pueden
verificar con la clave publica.

Es el unico servicio del proyecto que tiene la **clave privada**; nadie mas puede
firmar tokens.

## Stack

- FastAPI + Uvicorn
- `ldap3` para el *bind* contra LDAP
- `PyJWT` + `cryptography` para firmar RS256
- Docker (python:3.12-slim)

## Endpoints

| Metodo | Ruta | Descripcion |
| --- | --- | --- |
| `GET` | `/health` | Estado del servicio |
| `POST` | `/auth/login` | Valida contra LDAP y devuelve el JWT |

### POST /auth/login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"caleb","password":"caleb123"}'
```

```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9…",
  "token_type": "bearer",
  "expires_in": 1800,
  "username": "caleb",
  "dn": "uid=caleb,ou=users,dc=example,dc=com"
}
```

Respuestas: `200` con el token · `401` credenciales invalidas · `422` faltan campos.

## Claims

| Claim | Valor |
| --- | --- |
| `sub` | usuario LDAP (es la identidad que usa la API de items) |
| `dn` | `uid=<user>,ou=users,dc=example,dc=com` |
| `iss` | `jwt-ldap-auth` |
| `aud` | `jwt-items` (deja claro para que API es el token) |
| `iat`, `nbf`, `exp` | emision, valido desde y expiracion (30 min por defecto) |

## Como valida contra LDAP

1. Construye el DN del usuario: `uid=<username>,ou=users,dc=example,dc=com`.
2. Intenta `conn.bind(user_dn, password)`.
3. Si el bind falla, devuelve `401` generico (no revela si el usuario existe).
4. Si tiene exito, firma el JWT con la clave privada RSA.

```python
connection = Connection(server, user=user_dn, password=password, raise_exceptions=False)
authenticated = connection.bind()
```

## Variables de entorno

| Variable | Default | Descripcion |
| --- | --- | --- |
| `LDAP_HOST` | `openldap` | Servidor LDAP |
| `LDAP_PORT` | `389` | Puerto |
| `LDAP_BASE_DN` | `dc=example,dc=com` | Base del árbol |
| `LDAP_USERS_OU` | `ou=users` | OU donde viven los usuarios |
| `JWT_PRIVATE_KEY_FILE` | `/secrets/jwt_private.pem` | Clave privada (montada `:ro`) |
| `JWT_PUBLIC_KEY_FILE` | `/secrets/jwt_public.pem` | Clave publica |
| `JWT_ISSUER` | `jwt-ldap-auth` | Claim `iss` |
| `JWT_AUDIENCE` | `jwt-items` | Claim `aud` |
| `JWT_EXPIRE_MINUTES` | `30` | Vigencia del token |

## Correr con Docker

```bash
docker build -t jwt-ldap-auth .
docker run --rm -p 8000:8000 \
  -e LDAP_HOST=openldap \
  -v jwt_auth_secrets:/secrets:ro \
  jwt-ldap-auth
```

El volumen `jwt_auth_secrets` lo crea el `setup.sh` del proyecto raiz; contiene
las claves PEM y las contrasenas de LDAP y **no se versiona**.

## Desarrollo local

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export LDAP_HOST=localhost JWT_PRIVATE_KEY_FILE=./jwt_private.pem
uvicorn app.main:app --reload --port 8000
```

Documentacion interactiva: http://localhost:8000/docs

## Pruebas

```bash
python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt -r requirements-dev.txt

.venv/bin/python -m pytest                     # 5 unitarias (no necesita el stack)
RUN_INTEGRATION=1 .venv/bin/python -m pytest   # + 6 de integración contra :8000
```

Las unitarias generan una clave RSA en memoria y comprueban los claims
(`sub`, `dn`, `iss`, `aud`, `iat`, `nbf`, `exp` a 30 minutos), que el header sea
`RS256`, y que un token firmado con **otra** clave o con `alg:none` sea
rechazado. Las de integración hacen login real contra LDAP (usuario válido,
contraseña incorrecta, usuario inexistente) y verifican que el mensaje de error
no revela si el usuario existe.
