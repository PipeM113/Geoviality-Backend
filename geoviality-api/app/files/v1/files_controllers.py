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

# Crea un UUID
def create_uuid() -> str:
    return str(uuid.uuid4())

# Crea los directorios para almacenar las imágenes
def create_directories() -> None:
    base_dir = os.path.join(os.getcwd(), "services")
    imgs_dir = os.path.join(base_dir, "imgs")
    
    if not os.path.exists(base_dir):
        print("     -[API] Creando directorio en: ", base_dir)
        os.makedirs(base_dir, exist_ok=True)
    print("     -[API] Directorio base creado en: ", base_dir)
    if not os.path.exists(imgs_dir):
        print("     -[API] Creando directorio en: ", imgs_dir)
        os.makedirs(imgs_dir, exist_ok=True)
    print("     -[API] Directorio de imágenes creado en: ", imgs_dir)


# Envia los datos a la cola de RabbitMQ
def send_to_queue(data: PhotoQueue) -> bool:
    print (f"     -[API] Enviando datos: {data.id} ...") 
    print (f"     -[API] Enviando datos: {data.model_dump().keys()} ...")
    message = data.model_dump_json()
    try:
        conn = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
        channel = conn.channel()
        channel.queue_declare(queue='images', durable=True)
        print(f"    -[API] Enviando datos a la cola de RabbitMQ...")
        channel.basic_publish(
            exchange='',
            routing_key='images',
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2,
            )
        )
        channel.confirm_delivery()
        print(f"    -[API] Datos enviados a la cola de RabbitMQ.")
        conn.close()
        return True
    except AMQPError as e:
        print(f"    -[API] Error al enviar datos a la cola de RabbitMQ: {e}")
        return False
    except Exception as e:
        print(f"    -[API] Error al enviar datos a la cola de RabbitMQ: {e}")
        return False

# Recibe la imagen de la IA y la guarda
def receive_image_from_IA(photo: PhotoSave)-> None:
    image_filename = photo.id
    image = photo.image.encode('latin1')
    image_path = f"services/imgs/{image_filename}.jpg"
    with open(image_path, "wb") as f:
        f.write(image)
    print(f"    -[API] Imagen '{image_filename}' recibida y guardada en 'imgs'.")