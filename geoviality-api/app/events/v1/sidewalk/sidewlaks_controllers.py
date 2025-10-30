import uuid
import os
import socket
import pika
import dotenv
import asyncio
from db import db
from bson.objectid import ObjectId
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from jose.exceptions import JWTError, ExpiredSignatureError, JWTClaimsError
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from bson import SON
from pymongo.errors import PyMongoError
from pika.exceptions import AMQPError
import pytz

dotenv.load_dotenv()

from models import UserLogin, UserCreate, UserUpdate, TokenData, UserResponse, UserDB, User, PhotoQueue, PhotoSave, ListUserResponse, Geometry, SidewalksDB, Properties

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES",480))

pwd_context = CryptContext(schemes="bcrypt")

oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login")

event_queue1 = asyncio.Queue()

event_queue2 = asyncio.Queue()

chile_timezone = pytz.timezone("America/Santiago")

##################################################################################
# FUNCIONES VEREDAS
##################################################################################

def upload_sidewalk_to_mongodb(sidewalk: SidewalksDB) -> bool:
    collection = db['sidewalks']
    sidewalk = sidewalk.model_dump()
    sidewalk["_id"] = sidewalk["properties"]["id"]
    try:
        result = collection.insert_one(sidewalk)
        if result.inserted_id:
            return True
        return False
    except PyMongoError as e:
        print(f"    -[API] Error al subir vereda a MongoDB: {e}")
        return False

def actualizar_foto(foto: SidewalksDB, id_imagen: str)-> bool:
    """
    Actualiza la foto en la BD 'processed_images' agregando el id de la imagen a la lista de imagenes.
    """
    
    try:
        db.sidewalks.update_one(
            {"_id": foto.properties.id},
            {
                "$addToSet": {"properties.images": id_imagen},
                "$set": {"properties.last_update": datetime.now(chile_timezone)}
            }
        )
        print(f"    - [API] Foto.properties '{foto.properties.id}' actualizada con la imagen '{id_imagen}'.")
        return True
    except Exception as e:
        print(f"    - [API] Error al actualizar la foto '{foto.properties.id}': {e}")
        return False

def procesar(info: SidewalksDB):
    irregularidad = irregularidad_cercana(info.geometry)
    if irregularidad:
        print(f"    - [API] Irregularidad cercana a la imagen '{info.properties.id}' encontrada.")
        return actualizar_foto(irregularidad, info.properties.images[0])
    else:
        print(f"    - [API] No se encontró una irregularidad cercana a la imagen '{info.properties.id}'.")
        return upload_sidewalk_to_mongodb(info)

def irregularidad_cercana(punto: Geometry, max_distance=10) -> SidewalksDB | None :
    """
    Encuentra la irregularidad más cercana a un punto dado usando una consulta geoespacial.
    """
    try:
        punto = db.sidewalks.find_one({
            "geometry": {
                "$near": {
                    "$geometry": punto.model_dump(),
                    "$maxDistance": max_distance
                }
            }
        })
        return SidewalksDB(**punto)
    
    except Exception as e:
        print(f"    - [API] Error al buscar irregularidad cercana: {e}")
        return None