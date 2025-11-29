"""Esquemas del dominio auth (payloads y respuestas de autenticación)."""

# stdlib
from typing import Optional

# third-party
from pydantic import BaseModel, ConfigDict


class Token(BaseModel):
    """Token de acceso JWT."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Datos extraídos del token (por ahora solo username)."""
    username: Optional[str] = None


class UserLogin(BaseModel):
    """Credenciales de inicio de sesión."""
    username: str
    password: str


class UserPublic(BaseModel):
    """Perfil público básico del usuario autenticado."""
    model_config = ConfigDict(extra="allow")  # permite campos adicionales sin romper compat
    username: str
