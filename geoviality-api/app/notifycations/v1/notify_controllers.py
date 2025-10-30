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
# FUNCION SSE   
##################################################################################

# Generador de eventos para SSE
async def event_generator1():
    while True:
        data = await event_queue1.get()
        yield f"data: {data}\n\n"

async def event_generator2():
    while True:
        data = await event_queue2.get()
        yield f"data: {data}\n\n"
