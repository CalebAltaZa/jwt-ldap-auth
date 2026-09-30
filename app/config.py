import os
from pathlib import Path


def read_secret_file(path: str) -> str:
    """Read a secret from the mounted volume (never from the code or env)."""
    return Path(path).read_text().strip()


def env_int(name: str, default: int) -> int:
    return int(os.getenv(name, default))


# --- LDAP -------------------------------------------------------------------
LDAP_HOST = os.getenv("LDAP_HOST", "openldap")
LDAP_PORT = env_int("LDAP_PORT", 389)
LDAP_BASE_DN = os.getenv("LDAP_BASE_DN", "dc=example,dc=com")
LDAP_USERS_OU = os.getenv("LDAP_USERS_OU", "ou=users")

# --- JWT --------------------------------------------------------------------
# The RS256 key pair lives in a Docker volume that is mounted ONLY here, so
# this service is the only one able to SIGN tokens. `items` only gets the
# public key and therefore can only VALIDATE them.
JWT_PRIVATE_KEY_FILE = os.getenv("JWT_PRIVATE_KEY_FILE", "/secrets/jwt_private.pem")
JWT_PUBLIC_KEY_FILE = os.getenv("JWT_PUBLIC_KEY_FILE", "/secrets/jwt_public.pem")
JWT_ISSUER = os.getenv("JWT_ISSUER", "jwt-ldap-auth")
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE", "jwt-items")
JWT_EXPIRE_MINUTES = env_int("JWT_EXPIRE_MINUTES", 30)
