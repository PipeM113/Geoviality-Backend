import dotenv
import asyncio
import os
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
import pytz

dotenv.load_dotenv()

from .historical_querys import get_historical_data_query


SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES",480))

pwd_context = CryptContext(schemes="bcrypt")

oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login")

event_queue1 = asyncio.Queue()

event_queue2 = asyncio.Queue()

chile_timezone = pytz.timezone("America/Santiago")

##################################################################################
# FUNCIONES DATOS HISTORICOS
##################################################################################

# Obtiene los datos históricos
def obtener_datos_historicos():
    return get_historical_data_query()