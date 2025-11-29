"""Controladores del dominio users (sin acceso directo a DB)."""

from typing import List

from fastapi import HTTPException, status

from app.users.v1.users_schemas import UserCreate, UserUpdate, UserResponse
from app.users.v1.users_queries import (
    create_user,
    read_user,
    update_user,
    delete_user,
    read_all_users,
)
from app.auth.v1.auth_controllers import hash_password


def create_user_to_mongodb(payload: UserCreate) -> bool:
    """Crea un usuario nuevo; lanza 409 si el username ya existe."""
    if read_user(payload.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists",
        )
    doc = payload.model_dump()
    doc["password"] = hash_password(doc["password"])
    res = create_user(doc)
    return bool(res.inserted_id)


def read_user_from_mongodb(username: str) -> UserResponse | None:
    """Obtiene un usuario por username, o None si no existe."""
    doc = read_user(username)
    return UserResponse(**doc) if doc else None


def update_user_to_mongodb(username: str, changes: UserUpdate) -> bool:
    """Actualiza un usuario; hashea password si se incluye en el cambio."""
    doc = changes.model_dump(exclude_unset=True)
    if "password" in doc and doc["password"]:
        doc["password"] = hash_password(doc["password"])
    res = update_user(username, doc)
    return res.modified_count > 0


def delete_user_from_mongodb(username: str) -> bool:
    """Elimina un usuario por username; True si realmente lo borró."""
    res = delete_user(username)
    return res.deleted_count > 0


def read_all_users_from_mongodb() -> List[UserResponse]:
    """Devuelve todos los usuarios convertidos a UserResponse."""
    return [UserResponse(**d) for d in read_all_users()]
