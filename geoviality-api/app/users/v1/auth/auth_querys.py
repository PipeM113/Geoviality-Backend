from __future__ import annotations
from typing import Optional
from mongoengine.errors import MongoEngineException
from app.users.v1.user.user_model import UserDocument


class AuthQueryError(Exception):
    """Error base para operaciones de autenticación en MongoDB."""
    pass


def get_user_document_by_username(username: str) -> Optional[UserDocument]:
    try:
        return UserDocument.objects(username=username).first()
    except MongoEngineException as exc:
        raise AuthQueryError("No se pudo obtener el usuario desde la base de datos.") from exc
    except Exception as exc:
        raise AuthQueryError("Error inesperado al obtener el usuario.") from exc
