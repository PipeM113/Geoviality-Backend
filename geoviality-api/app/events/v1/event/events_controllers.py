import uuid
import os
import dotenv
import asyncio
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from jose.exceptions import JWTError, ExpiredSignatureError, JWTClaimsError
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from pymongo.errors import PyMongoError
import pytz

dotenv.load_dotenv()

from .events_schemas import Geometry, User
from .events_querys import find_street_near_geometry, update_street_by_id, get_current_active_user

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES",480))

pwd_context = CryptContext(schemes="bcrypt")

oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login")

event_queue1 = asyncio.Queue()

event_queue2 = asyncio.Queue()

chile_timezone = pytz.timezone("America/Santiago")

def normalize_types(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    return sorted({
        str(tipo).strip().capitalize()
        for tipo in value
        if str(tipo).strip()
    })

##################################################################################
# FUNCIONES STREETS
##################################################################################

# Encuentra la calle más cercana a un punto dado
def encontrar_calle_mas_cercana(punto: Geometry, max_distance=30) -> Optional[dict]:
    """
    Encuentra la calle más cercana a un punto dado usando una consulta geoespacial.
    """
    try:
        return find_street_near_geometry(punto.model_dump(), max_distance)
    except PyMongoError as e:
        print(f"    -[API] Error al encontrar calle más cercana en MongoDB: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while finding the nearest street.",
        )
    except Exception as e:
        print(f"    -[API] Error inesperado al encontrar calle más cercana: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while finding the nearest street.",
        )

# Borra los tipos anteriores de una calle
def borrar_ant_calles(id_calle: str, ant_tipos: list):
    decrementos = {f"properties.{tipo}": -1 for tipo in normalize_types(ant_tipos)}
    if not decrementos:
        return
    try:
        update_street_by_id(id_calle, inc=decrementos)
    except PyMongoError as e:
        print(f"    -[API] Error al borrar antiguos tipos de calle en MongoDB: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while updating street types.",
        )
    except Exception as e:
        print(f"    -[API] Error inesperado al borrar antiguos tipos de calle: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while updating street types.",
        )

# Modifica la calle si se modifica la info de un punto
def modificar_calles(
    id_imagen: str,
    punto: Geometry,
    types: list[str] | str | None,
    ant_types: list[str] | str | None,
    state: Optional[int],
    ant_state: int,
):
    calle = encontrar_calle_mas_cercana(punto)
    if not calle:
        return
    id_calle = calle["id"]
    ant_types_norm = normalize_types(ant_types)
    types_provided = types is not None
    new_types_norm = normalize_types(types) if types_provided else ant_types_norm
    types_changed = types_provided and new_types_norm != ant_types_norm
    now = datetime.now(chile_timezone)

    if state is not None and state != ant_state:
        if state == 1:
            borrar_ant_calles(id_calle, ant_types_norm)
            try:
                update_street_by_id(
                    id_calle,
                    pull={"properties.images": id_imagen},
                    set_fields={"properties.last_update": now}
                )
            except PyMongoError as e:
                print(f"    -[API] Error al actualizar calle en MongoDB: {e}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update street data.")
            except Exception as e:
                print(f"    -[API] Error al actualizar calle en MongoDB: {e}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while updating street data.")
        else:
            if types_changed and ant_types_norm:
                borrar_ant_calles(id_calle, ant_types_norm)
            incrementos = {f"properties.{tipo}": 1 for tipo in new_types_norm} if new_types_norm else None
            push_payload = {"properties.images": id_imagen} if new_types_norm else None
            pull_payload = {"properties.images": id_imagen} if not new_types_norm else None
            try:
                update_street_by_id(
                    id_calle,
                    inc=incrementos,
                    push=push_payload,
                    pull=pull_payload,
                    set_fields={"properties.last_update": now}
                )
            except PyMongoError as e:
                print(f"    -[API] Error al actualizar calle en MongoDB: {e}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update street data.")
            except Exception as e:
                print(f"    -[API] Error al actualizar calle en MongoDB: {e}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while updating street data.")
    else:
        if types_changed and ant_state == 0:
            if ant_types_norm:
                borrar_ant_calles(id_calle, ant_types_norm)
            incrementos = {f"properties.{tipo}": 1 for tipo in new_types_norm} if new_types_norm else None
            push_payload = {"properties.images": id_imagen} if new_types_norm else None
            pull_payload = {"properties.images": id_imagen} if not new_types_norm else None
            try:
                update_street_by_id(
                    id_calle,
                    inc=incrementos,
                    push=push_payload,
                    pull=pull_payload,
                    set_fields={"properties.last_update": now}
                )
            except PyMongoError as e:
                print(f"    -[API] Error al actualizar calle en MongoDB: {e}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update street data.")
            except Exception as e:
                print(f"    -[API] Error al actualizar calle en MongoDB: {e}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while updating street data.")

# Elimina la información de un punto de las calles
def eliminar_de_calles(id_imagen:str, punto:Geometry, tipos: list):
    tipos_norm = normalize_types(tipos)
    decrementos = {f"properties.{tipo}": -1 for tipo in tipos_norm} if tipos_norm else None
    calle = encontrar_calle_mas_cercana(punto)
    if not calle:
        return
    id_calle = calle["id"]
    try:
        update_street_by_id(
            id_calle,
            inc=decrementos,
            pull={"properties.images": id_imagen}
        )
    except PyMongoError as e:
        print(f"    -[API] Error al eliminar tipos de calle en MongoDB: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while removing street data.",
        )
    except Exception as e:
        print(f"    -[API] Error inesperado al eliminar tipos de calle: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while removing street data.",
        )