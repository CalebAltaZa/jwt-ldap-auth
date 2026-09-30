"""Pruebas del servicio de autenticación.

Se ejecutan de dos formas:

* Sin nada levantado (por defecto): pruebas unitarias de los claims y de la
  construcción del DN, con una clave RSA generada en memoria.
* Con el stack docker levantado: pruebas de integración contra
  http://localhost:8000 (`docker compose up -d` en la raíz del proyecto).

    pytest -q                      # sólo unitarias
    RUN_INTEGRATION=1 pytest -q     # unitarias + integración
"""

import os

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.config import JWT_AUDIENCE, JWT_EXPIRE_MINUTES, JWT_ISSUER
from app.security import build_user_dn, create_access_token

RUN_INTEGRATION = os.getenv("RUN_INTEGRATION") == "1"
AUTH_URL = os.getenv("AUTH_URL", "http://localhost:8000")

TEST_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
TEST_PRIVATE_PEM = TEST_KEY.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
).decode()
TEST_PUBLIC_PEM = TEST_KEY.public_key().public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo,
).decode()


# --------------------------------------------------------------------------
# Unitarias
# --------------------------------------------------------------------------
def test_build_user_dn():
    assert build_user_dn("caleb") == "uid=caleb,ou=users,dc=example,dc=com"


def test_create_access_token_claims(monkeypatch):
    monkeypatch.setattr("app.security.private_key", lambda: TEST_PRIVATE_PEM)

    token = create_access_token("caleb", build_user_dn("caleb"))
    claims = jwt.decode(
        token,
        TEST_PUBLIC_PEM,
        algorithms=["RS256"],
        audience=JWT_AUDIENCE,
        issuer=JWT_ISSUER,
    )

    assert claims["sub"] == "caleb"
    assert claims["dn"] == "uid=caleb,ou=users,dc=example,dc=com"
    assert claims["iss"] == JWT_ISSUER
    assert claims["aud"] == JWT_AUDIENCE
    assert claims["exp"] - claims["iat"] == JWT_EXPIRE_MINUTES * 60


def test_token_is_signed_with_rs256(monkeypatch):
    monkeypatch.setattr("app.security.private_key", lambda: TEST_PRIVATE_PEM)
    header = jwt.get_unverified_header(create_access_token("caleb", "dn"))
    assert header["alg"] == "RS256"


def test_token_from_other_key_is_rejected(monkeypatch):
    """La firma es lo que impide que otro emisor fabrique tokens."""
    monkeypatch.setattr("app.security.private_key", lambda: TEST_PRIVATE_PEM)
    token = create_access_token("caleb", "dn")

    other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    other_public_pem = other_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()

    with pytest.raises(jwt.InvalidSignatureError):
        jwt.decode(
            token,
            other_public_pem,
            algorithms=["RS256"],
            audience=JWT_AUDIENCE,
            issuer=JWT_ISSUER,
        )


def test_alg_none_is_rejected(monkeypatch):
    """`alg: none` es el ataque clásico contra los JWT."""
    forged = jwt.encode(
        {"sub": "admin", "iss": JWT_ISSUER, "aud": JWT_AUDIENCE},
        key="",
        algorithm="none",
    )
    with pytest.raises(jwt.InvalidAlgorithmError):
        jwt.decode(forged, TEST_PUBLIC_PEM, algorithms=["RS256"], audience=JWT_AUDIENCE)


# --------------------------------------------------------------------------
# Integración (requiere el stackdocker levantado)
# --------------------------------------------------------------------------
requires_stack = pytest.mark.skipif(
    not RUN_INTEGRATION, reason="requiere RUN_INTEGRATION=1 y el stack levantado"
)


@requires_stack
def test_health():
    import httpx

    response = httpx.get(f"{AUTH_URL}/health", timeout=10)
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@requires_stack
def test_login_ok_and_claims():
    import httpx

    response = httpx.post(
        f"{AUTH_URL}/auth/login",
        json={"username": "caleb", "password": "caleb123"},
        timeout=15,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["username"] == "caleb"
    assert body["dn"] == "uid=caleb,ou=users,dc=example,dc=com"
    assert body["access_token"].count(".") == 2

    header = jwt.get_unverified_header(body["access_token"])
    assert header["alg"] == "RS256"

    public_pem = os.popen(
        "docker run --rm -v jwt_auth_secrets:/secrets alpine cat /secrets/jwt_public.pem"
    ).read()
    claims = jwt.decode(
        body["access_token"],
        public_pem,
        algorithms=["RS256"],
        audience=JWT_AUDIENCE,
        issuer=JWT_ISSUER,
    )
    assert claims["sub"] == "caleb"


@requires_stack
@pytest.mark.parametrize("username,password", [
    ("caleb", "incorrecta"),
    ("noexiste", "caleb123"),
    ("", ""),
])
def test_login_rechaza_credenciales_invalidas(username, password):
    import httpx

    response = httpx.post(
        f"{AUTH_URL}/auth/login",
        json={"username": username, "password": password},
        timeout=15,
    )
    assert response.status_code in (401, 422)


@requires_stack
def test_login_no_revela_si_el_usuario_existe():
    """Mismo mensaje para usuario inexistente y contraseña incorrecta."""
    import httpx

    wrong_password = httpx.post(
        f"{AUTH_URL}/auth/login", json={"username": "caleb", "password": "x" * 8}, timeout=15
    ).json()
    missing_user = httpx.post(
        f"{AUTH_URL}/auth/login", json={"username": "fantasma", "password": "x" * 8}, timeout=15
    ).json()
    assert wrong_password["detail"] == missing_user["detail"]
