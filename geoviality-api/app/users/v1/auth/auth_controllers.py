from __future__ import annotations
import os
from typing import Annotated
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from jose.exceptions import JWTError, ExpiredSignatureError, JWTClaimsError
import pytz
from passlib.context import CryptContext

from app.users.v1.auth.auth_querys import get_user_document_by_username, AuthQueryError
from app.users.v1.user.users_schemas import User
from app.users.v1.user.user_model import UserDocument
from app.users.v1.auth.auth_schemas import TokenData, UserLogin
from app.users.v1.user.users_schemas import UserResponse


SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 480))

pwd_context = CryptContext(schemes=["bcrypt"])

oauth2 = OAuth2PasswordBearer(tokenUrl="/v1/auth/login")

chile_timezone = pytz.timezone("America/Santiago")

def _serialize_user_document(user_doc: UserDocument, include_password: bool = False) -> dict:
    user_dict = user_doc.to_mongo().to_dict()
    user_dict["_id"] = str(user_doc.id)
    if not include_password:
        user_dict.pop("password", None)
    return user_dict

##################################################################################
# TOKEN FUNCS
##################################################################################

# Crea un token de acceso
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(chile_timezone) + expires_delta
    else:
        expire = datetime.now(chile_timezone) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user_from_mongodb(username: str) -> UserDocument | None:
    try:
        return get_user_document_by_username(username)
    except AuthQueryError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al consultar el usuario en la base de datos.",
        ) from exc

def verify_password(password, hashed_password) -> bool:
    return pwd_context.verify(password, hashed_password)

def authenticate_user(userLog: UserLogin) -> UserResponse | None:
    user_doc = get_user_from_mongodb(userLog.username)
    if not user_doc:
        return None
    if not verify_password(userLog.password, user_doc.password):
        return None
    return UserResponse(**_serialize_user_document(user_doc))

# Obtiene el usuario actual
async def get_current_user(token: Annotated[str,Depends(oauth2)]) -> User:
    credentials_exception = HTTPException( 
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except JWTClaimsError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token claims")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = get_user_from_mongodb(username=token_data.username)
    if user is None:
        raise credentials_exception
    return User(**_serialize_user_document(user))

# Obtiene el usuario actual activo
async def get_current_active_user(current_user: Annotated[User,Depends(get_current_user)]) -> User:
    if current_user.disabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user