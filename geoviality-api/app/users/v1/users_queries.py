"""Consultas a MongoDB para el dominio users."""

# stdlib
from typing import Optional, Dict, Any, List

# locales
from app.core.database import db

COL = "users"


def create_user(doc: Dict[str, Any]):
    """Inserta un usuario en la colección."""
    return db[COL].insert_one(doc)


def read_user(username: str) -> Optional[Dict[str, Any]]:
    """Busca un usuario por username."""
    return db[COL].find_one({"username": username})


def update_user(username: str, changes: Dict[str, Any]):
    """Actualiza campos de un usuario por username."""
    return db[COL].update_one({"username": username}, {"$set": changes})


def delete_user(username: str):
    """Elimina un usuario por username."""
    return db[COL].delete_one({"username": username})


def read_all_users() -> List[Dict[str, Any]]:
    """Devuelve todos los usuarios como documentos crudos."""
    return list(db[COL].find({}))
