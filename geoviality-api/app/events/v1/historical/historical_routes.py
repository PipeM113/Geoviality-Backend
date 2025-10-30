from fastapi import APIRouter, File, UploadFile, Request, Depends, status, Form, WebSocket, WebSocketDisconnect
from datetime import datetime, timedelta
import os
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2PasswordRequestForm
import dotenv
from typing import Annotated, List
import pytz

dotenv.load_dotenv()

from db import db
from controllers import create_uuid, send_to_queue
from controllers import create_user_to_mongodb, read_user_from_mongodb, update_user_to_mongodb, delete_user_from_mongodb
from controllers import authenticate_user, create_access_token, get_current_active_user, receive_image_from_IA
from controllers import read_all_users_from_mongodb,modificar_calles , event_generator1, event_generator2 , obtener_datos_historicos, eliminar_de_calles, test, encontrar_calle_mas_cercana
from controllers import ACCESS_TOKEN_EXPIRE_MINUTES, event_queue1, event_queue2 , procesar
from .historical_schemas import DatosHistoricos, DatosHistoricosResponse
from .historical_models import User

historical_router = APIRouter(prefix="/v1/historical", tags=["historical"])

##################################################################################
# RUTAS DATOS HISTÓRICOS
################################################################################## 

# Obtiene los datos históricos
@historical_router.get("/data/historical_data")
async def get_historical_data(user: User = Depends(get_current_active_user)) -> list[DatosHistoricos]:
    data = DatosHistoricosResponse(info = obtener_datos_historicos())
    return data.info