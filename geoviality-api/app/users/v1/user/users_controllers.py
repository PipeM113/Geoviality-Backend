import uuid
import os
import socket
import pika
import dotenv
import asyncio
from typing import Annotated
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from jose.exceptions import JWTError, ExpiredSignatureError, JWTClaimsError
from passlib.context import CryptContext
from pika.exceptions import AMQPError
import pytz

from users_querys import (
    create_user_document,
    delete_user_document,
    get_user_document_by_username,
    list_user_documents,
    update_user_document,
    UserQueryError,
)
from auth.auth_schemas import TokenData, UserLogin
from users_schemas import (
    ListUserResponse,
    User,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from user_model import UserDocument

dotenv.load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 480))

pwd_context = CryptContext(schemes=["bcrypt"])

oauth2 = OAuth2PasswordBearer(tokenUrl="/v1/auth/login")

event_queue1 = asyncio.Queue()
event_queue2 = asyncio.Queue()

chile_timezone = pytz.timezone("America/Santiago")


def _serialize_user_document(user_doc: UserDocument, include_password: bool = False) -> dict:
    user_dict = user_doc.to_mongo().to_dict()
    user_dict["_id"] = str(user_doc.id)
    if not include_password:
        user_dict.pop("password", None)
    return user_dict


##################################################################################
# FUNCIONES PARA AUTENTICACIÓN
##################################################################################


def get_user_from_mongodb(username: str) -> UserDocument | None:
    try:
        return get_user_document_by_username(username)
    except UserQueryError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al consultar el usuario en la base de datos.",
        ) from exc


def encrypt_password(password: str) -> str:
    return pwd_context.hash(password)


def authenticate_user(userLog: UserLogin) -> UserResponse | None:
    user_doc = get_user_from_mongodb(userLog.username)
    if not user_doc:
        return None
    if not verify_password(userLog.password, user_doc.password):
        return None
    return UserResponse(**_serialize_user_document(user_doc))


def verify_password(password, hashed_password) -> bool:
    return pwd_context.verify(password, hashed_password)


#################################################################################
# FUNCIONES CRUD USUARIOS
##################################################################################


def create_user_to_mongodb(user: UserCreate) -> bool:
    if get_user_from_mongodb(user.username):
        return False
    hash_password = encrypt_password(user.password)
    user_dict = user.model_dump()
    user_dict.pop("password", None)
    user_dict.update(
        {
            "password": hash_password,
            "date_register": datetime.now(chile_timezone),
            "disabled": False,
        }
    )
    try:
        return create_user_document(user_dict)
    except UserQueryError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al crear el usuario en la base de datos.",
        ) from exc


def read_user_from_mongodb(username: str) -> UserResponse | None:
    user = get_user_from_mongodb(username)
    if not user:
        return None
    user_dict = _serialize_user_document(user)
    return UserResponse(**user_dict)


def update_user_to_mongodb(user: UserUpdate) -> bool:
    update_data = user.model_dump(exclude_none=True)
    username = update_data.pop("username")
    if "password" in update_data:
        update_data["password"] = encrypt_password(update_data["password"])
    try:
        return update_user_document(username, update_data)
    except UserQueryError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al actualizar el usuario en la base de datos.",
        ) from exc


def delete_user_from_mongodb(username: str) -> bool:
    try:
        return delete_user_document(username)
    except UserQueryError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al eliminar el usuario en la base de datos.",
        ) from exc


def read_all_users_from_mongodb() -> list[UserResponse]:
    try:
        users = list_user_documents()
    except UserQueryError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al listar los usuarios en la base de datos.",
        ) from exc
    serialized_users = [_serialize_user_document(user) for user in users]
    retUsers = ListUserResponse(info=serialized_users)
    return retUsers.info