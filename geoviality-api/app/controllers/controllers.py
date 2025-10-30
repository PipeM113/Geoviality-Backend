import uuid
import os
import socket
import pika
import dotenv
import asyncio
from ..db import db
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
# FUNCIONES IMAGENES
##################################################################################

# Obtiene la IP local
def get_local_ip() -> str:
    print("     -[API] Usando IP LOCAL - IP...")
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.254.254.254', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip