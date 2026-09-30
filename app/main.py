"""LDAP Auth API: valida credenciales contra OpenLDAP y devuelve un JWT (RS256)."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .config import JWT_AUDIENCE, JWT_EXPIRE_MINUTES, JWT_ISSUER
from .security import authenticate_ldap, create_access_token

app = FastAPI(
    title="LDAP Auth API",
    description=(
        "Valida las credenciales del usuario contra OpenLDAP (bind) y, si son "
        "correctas, emite un JWT firmado con RS256."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, examples=["caleb"])
    password: str = Field(min_length=1, examples=["caleb123"])


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    username: str
    dn: str


@app.get("/health")
def health():
    return {"status": "ok", "service": "auth", "issuer": JWT_ISSUER}


@app.post("/auth/login", response_model=LoginResponse)
def login(request: LoginRequest):
    ok, dn = authenticate_ldap(request.username, request.password)
    if not ok:
        # Generic message on purpose: we do not reveal whether the user exists.
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return LoginResponse(
        access_token=create_access_token(request.username, dn),
        expires_in=JWT_EXPIRE_MINUTES * 60,
        username=request.username,
        dn=dn,
    )
