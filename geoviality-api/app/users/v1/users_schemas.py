"""Esquemas Pydantic del dominio users."""

# stdlib
from typing import Optional, List

# third-party
from pydantic import BaseModel, ConfigDict


class User(BaseModel):
    """Entidad genérica de usuario (modelo flexible)."""
    model_config = ConfigDict(extra="allow")
    username: str


class UserCreate(BaseModel):
    """Payload para creación de usuario."""
    username: str
    password: str
    # agrega aquí los campos exactos que ya usas (email, role, etc.)


class UserUpdate(BaseModel):
    """Payload para actualización parcial de usuario."""
    password: Optional[str] = None
    # agrega aquí campos opcionales actualizables


class UserResponse(BaseModel):
    """Respuesta pública de usuario."""
    model_config = ConfigDict(extra="allow")
    username: str


class ListUserResponse(BaseModel):
    """Contenedor para lista de usuarios."""
    users: List[UserResponse]
