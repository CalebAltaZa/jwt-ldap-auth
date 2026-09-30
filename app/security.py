"""LDAP authentication + RS256 token issuing."""

import datetime as dt
from functools import lru_cache

import jwt
from ldap3 import ALL, Connection, Server

from .config import (
    JWT_AUDIENCE,
    JWT_EXPIRE_MINUTES,
    JWT_ISSUER,
    JWT_PRIVATE_KEY_FILE,
    LDAP_BASE_DN,
    LDAP_HOST,
    LDAP_PORT,
    LDAP_USERS_OU,
    read_secret_file,
)


def build_user_dn(username: str) -> str:
    return f"uid={username},{LDAP_USERS_OU},{LDAP_BASE_DN}"


@lru_cache(maxsize=1)
def private_key() -> str:
    """Loaded once and cached: the private key never leaves this service."""
    return read_secret_file(JWT_PRIVATE_KEY_FILE)


def authenticate_ldap(username: str, password: str) -> tuple[bool, str]:
    """Try to bind as the user. Returns (ok, dn)."""
    dn = build_user_dn(username)
    server = Server(LDAP_HOST, port=LDAP_PORT, get_info=ALL)
    connection = Connection(
        server, user=dn, password=password, auto_bind=False, raise_exceptions=False
    )
    try:
        return (True, dn) if connection.bind() else (False, dn)
    finally:
        try:
            connection.unbind()
        except Exception:
            pass


def create_access_token(username: str, dn: str) -> str:
    """Sign a JWT (RS256) with the private key from the secrets volume."""
    now = dt.datetime.now(dt.timezone.utc)
    payload = {
        "sub": username,          # subject: who the token represents
        "dn": dn,                 # full LDAP DN of the authenticated user
        "iss": JWT_ISSUER,        # who issued it
        "aud": JWT_AUDIENCE,      # who is allowed to consume it
        "iat": now,               # issued at
        "nbf": now,               # not valid before
        "exp": now + dt.timedelta(minutes=JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, private_key(), algorithm="RS256")
