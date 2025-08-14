# app/security.py
"""
Seguridad (Auth, Roles y Tokens) - DEMO
---------------------------------------
Este módulo implementa autenticación con JWT y control de acceso por roles
(usando FastAPI + HTTPBearer), con contraseñas cifradas (bcrypt) y verificación
de tokens. Los usuarios se definen en una "base de datos dummy" en memoria
solo para propósitos de demostración.

⚠ En producción:
- Usar una base de datos real (SQL o NoSQL) para persistir usuarios y registros.
- Proteger el JWT_SECRET, reducir expiración de tokens, y servir bajo HTTPS.
- Implementar registro, recuperación de contraseñas, rotación de secretos y
  controles de acceso avanzados.
"""
from datetime import datetime, timedelta
from typing import Optional, Literal

import os
from fastapi import HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError
from passlib.context import CryptContext

# Config
SECRET_KEY = os.getenv("JWT_SECRET", "change-this-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = int(os.getenv("JWT_EXPIRE_MIN", "480"))  # 8h por defecto

# Demo store
# contraseña: "promotor123" y "medico123" (hash real abajo)
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
USERS = {
    "promotor": {
        "username": "promotor",
        "full_name": "Promotor",
        "role": "promotor",
        "hashed_password": pwd_ctx.hash("promotor123"),
        "disabled": False,
    },
    "medico": {
        "username": "medico",
        "full_name": "Médico",
        "role": "medico",
        "hashed_password": pwd_ctx.hash("medico123"),
        "disabled": False,
    },
    "admin": {
        "username": "admin",
        "full_name": "Admin",
        "role": "admin",
        "hashed_password": pwd_ctx.hash("admin123"),
        "disabled": False,
    },
}

bearer_scheme = HTTPBearer(auto_error=True)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)

def authenticate_user(username: str, password: str) -> Optional[dict]:
    u = USERS.get(username)
    if not u or not verify_password(password, u["hashed_password"]) or u.get("disabled"):
        return None
    return u

def create_access_token(sub: str, role: str) -> str:
    exp = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_MINUTES)
    to_encode = {"sub": sub, "role": role, "exp": exp}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(creds: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    token = creds.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None or role is None:
            raise HTTPException(status_code=401, detail="Token inválido")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    u = USERS.get(username)
    if not u or u.get("disabled"):
        raise HTTPException(status_code=401, detail="Usuario inactivo")
    return {"username": username, "role": role, "full_name": u.get("full_name")}

def require_roles(*allowed: Literal["promotor","medico","admin"]):
    def _dep(user: dict = Depends(get_current_user)) -> dict:
        if user["role"] not in allowed:
            raise HTTPException(status_code=403, detail="Permisos insuficientes")
        return user
    return _dep