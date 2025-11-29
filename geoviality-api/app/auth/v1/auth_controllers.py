"""Controladores de autenticación (hash de contraseñas, JWT y dependencias OAuth2)."""

from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional, Dict, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from jose.exceptions import JWTError, ExpiredSignatureError
from passlib.context import CryptContext

from app.core.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from app.auth.v1.auth_schemas import UserLogin, UserPublic
from app.auth.v1.auth_queries import get_user_by_username

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Prefijo /v1 está en routes; aquí solo declaramos la dependencia
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/login")


def hash_password(plain_password: str) -> str:
    """Hashea un password en bcrypt."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica que el password plano coincida con el hash almacenado."""
    return pwd_context.verify(plain_password, hashed_password)


def authenticate_user(creds: UserLogin) -> Optional[Dict[str, Any]]:
    """Autentica un usuario usando username y password. Devuelve el documento o None."""
    user_doc = get_user_by_username(creds.username)
    if not user_doc:
        return None
    if not verify_password(creds.password, user_doc.get("password", "")):
        return None
    return user_doc


def create_access_token(data: dict, expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    """Crea un JWT de acceso con expiración en minutos."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> UserPublic:
    """Obtiene el usuario actual a partir del token Bearer, o lanza 401 si no es válido."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
    except (ExpiredSignatureError, JWTError) as exc:
        # Encadenamos la excepción original para mejor trazabilidad
        raise credentials_exception from exc

    user_doc = get_user_by_username(username)
    if not user_doc:
        raise credentials_exception

    return UserPublic(**user_doc)


async def get_current_active_user(
    current_user: Annotated[UserPublic, Depends(get_current_user)]
) -> UserPublic:
    """Devuelve el usuario actual ya validado (puedes agregar checks extra si quisieras)."""
    # Mantengo la misma lógica que tenías: reconstruir el modelo desde el actual.
    return UserPublic(**current_user.model_dump())
