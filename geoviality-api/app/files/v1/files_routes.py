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
from files_schemas import UserCreate, UserUpdate, Token, UserSol, UserLogin, User, PhotoQueue, InfoUpdate, PhotoSave, Geometry

file_router = APIRouter(prefix="/v1/files", tags=["files"])

##################################################################################
# RUTAS Archivos
##################################################################################

# Sube una imagen a 'pre_pro' y envía la información a la cola de RabbitMQ
@file_router.post("/upload/image", status_code=status.HTTP_201_CREATED)
async def upload_image(
    image: UploadFile = File(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    date: str = Form(...),
    modo: str = Form(...),
    user: User = Depends(get_current_active_user)
):
    date = datetime.fromisoformat(date)
    _id = create_uuid()
    image_data = await image.read()
    photo_data = PhotoQueue(
        id = _id,
        image = image_data.decode('latin1'),
        latitude = latitude,
        longitude = longitude,
        date = date,
        modo = modo,
        user= user.username
    )
    print( f"    - [API] Enviando imagen '{_id}' a la cola de RabbitMQ.")
    res = send_to_queue(photo_data)
    if res:
        return {"message": f"Photo uploaded successfully with id: {_id}"}
    else:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error uploading data")

# Descarga la imagen 'image_id' de 'post_pro'
@file_router.get("/download/get_image/{image_id}")
async def download_image(request: Request, user: User = Depends(get_current_active_user)) -> FileResponse:
    image_id = request.path_params['image_id']
    file_path = os.path.join(os.getcwd(),f"services/imgs/{image_id}.jpg")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    return FileResponse(file_path)

# Obtener una imagen procesada de la IA
@file_router.post("/data/processed_image")
async def get_processed_image(data: PhotoSave):
    receive_image_from_IA(data)
    photo = db.processed_geojson.find_one({"properties.images": data.id})
    if photo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
    photo = PhotoDB(**photo)
    await event_queue1.put(photo.model_dump_json())
    await event_queue2.put(photo.model_dump_json())
    return {"message": "Image received successfully"}