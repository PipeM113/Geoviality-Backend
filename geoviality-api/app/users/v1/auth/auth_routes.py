from datetime import timedelta
from typing import Annotated

import dotenv
from fastapi import APIRouter, Depends, Form, status
from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from controllers import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from schemas.v1.auth_schemas import Token, UserLogin
from schemas.v1.users_schemas import User

dotenv.load_dotenv()

auth_router = APIRouter(prefix="/v1/auth", tags=["auth"])

##################################################################################
# RUTAS LOGIN
##################################################################################

# Login
@auth_router.post("/login")
async def login(userReq: OAuth2PasswordRequestForm = Depends(), tipo: str = Form(...)) -> Token:
    try:
        user = authenticate_user(UserLogin(username=userReq.username, password=userReq.password))
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno durante la autenticación.") from exc
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.tipo < int(tipo):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authorized",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return Token(access_token=access_token, token_type="bearer")

# Ruta de verificación de usuario
@auth_router.get("/users/me/")
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user
