from __future__ import annotations
from typing import Dict, List, Optional
from mongoengine.errors import MongoEngineException
from user_model import UserDocument


class UserQueryError(Exception):
    """Error base para operaciones de usuarios en MongoDB."""
    pass


def get_user_document_by_username(username: str) -> Optional[UserDocument]:
    try:
        return UserDocument.objects(username=username).first()
    except MongoEngineException as exc:
        raise UserQueryError("No se pudo obtener el usuario desde la base de datos.") from exc
    except Exception as exc:
        raise UserQueryError("Error inesperado al obtener el usuario.") from exc


def create_user_document(user_data: Dict) -> bool:
    try:
        user_document = UserDocument(**user_data)
        user_document.save()
        return True
    except MongoEngineException as exc:
        raise UserQueryError("No se pudo crear el usuario en la base de datos.") from exc
    except Exception as exc:
        raise UserQueryError("Error inesperado al crear el usuario.") from exc


def update_user_document(username: str, update_data: Dict) -> bool:
    if not update_data:
        return True
    try:
        update_ops = {f"set__{field}": value for field, value in update_data.items()}
        updated = UserDocument.objects(username=username).update_one(**update_ops)
        return updated > 0
    except MongoEngineException as exc:
        raise UserQueryError("No se pudo actualizar el usuario en la base de datos.") from exc
    except Exception as exc:
        raise UserQueryError("Error inesperado al actualizar el usuario.") from exc


def delete_user_document(username: str) -> bool:
    try:
        deleted = UserDocument.objects(username=username).delete()
        return deleted > 0
    except MongoEngineException as exc:
        raise UserQueryError("No se pudo eliminar el usuario de la base de datos.") from exc
    except Exception as exc:
        raise UserQueryError("Error inesperado al eliminar el usuario.") from exc


def list_user_documents() -> List[UserDocument]:
    try:
        return list(UserDocument.objects())
    except MongoEngineException as exc:
        raise UserQueryError("No se pudo listar los usuarios desde la base de datos.") from exc
    except Exception as exc:
        raise UserQueryError("Error inesperado al listar los usuarios.") from exc