"""Consultas de acceso a datos para el dominio auth (usuarios)."""

# stdlib
from typing import Optional, Dict, Any

# locales
from app.core.database import db

# Acceso a la colección de usuarios; adapta el nombre si tu colección difiere
USERS_COL = "users"


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Obtiene un documento de usuario por username desde la colección de usuarios."""
    return db[USERS_COL].find_one({"username": username})
