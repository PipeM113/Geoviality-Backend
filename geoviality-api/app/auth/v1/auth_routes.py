"""Rutas del dominio auth (inicio de sesión y perfil del usuario autenticado)."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.auth.v1.auth_controllers import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
)
from app.auth.v1.auth_schemas import Token, UserLogin, UserPublic

router = APIRouter(
    prefix="/v1/auth",
    tags=["auth"],
)


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Token:
    """Endpoint de login OAuth2 (username/password → JWT Bearer)."""
    user_doc = authenticate_user(
        UserLogin(username=form_data.username, password=form_data.password)
    )
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token({"sub": user_doc["username"]})
    return Token(access_token=access_token)


@router.get("/users/me/", response_model=UserPublic)
async def users_me(current: UserPublic = Depends(get_current_active_user)) -> UserPublic:
    """Devuelve el usuario actualmente autenticado."""
    return current
