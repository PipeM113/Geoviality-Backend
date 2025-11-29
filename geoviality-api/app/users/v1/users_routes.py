"""Rutas del dominio users (prefix='/v1/users')."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.v1.auth_controllers import get_current_active_user
from app.users.v1.users_schemas import UserCreate, UserUpdate, UserResponse
from app.users.v1.users_controllers import (
    create_user_to_mongodb,
    read_user_from_mongodb,
    update_user_to_mongodb,
    delete_user_from_mongodb,
    read_all_users_from_mongodb,
)

router = APIRouter(
    prefix="/v1/users",
    tags=["users"],
)


@router.post("/create")
async def create_user(u: UserCreate) -> dict:
    """Crea un usuario nuevo."""
    ok = create_user_to_mongodb(u)
    return {"created": ok}


@router.get("/read/{username}", response_model=UserResponse | None)
async def read_user(username: str, _=Depends(get_current_active_user)):
    """Lee un usuario por username (requiere autenticación)."""
    return read_user_from_mongodb(username)


@router.put("/update/{username}")
async def update_user(
    username: str,
    u: UserUpdate,
    _=Depends(get_current_active_user),
) -> dict:
    """Actualiza datos de un usuario (requiere autenticación)."""
    ok = update_user_to_mongodb(username, u)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found or unchanged",
        )
    return {"updated": True}


@router.delete("/delete/{username}")
async def delete_user(username: str, _=Depends(get_current_active_user)) -> dict:
    """Elimina un usuario (requiere autenticación)."""
    ok = delete_user_from_mongodb(username)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return {"deleted": True}


@router.get("/read_all", response_model=List[UserResponse])
async def read_all(_=Depends(get_current_active_user)):
    """Devuelve todos los usuarios (requiere autenticación)."""
    return read_all_users_from_mongodb()
