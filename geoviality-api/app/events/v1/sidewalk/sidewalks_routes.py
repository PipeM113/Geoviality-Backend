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
from models import UserCreate, UserUpdate, Token, UserSol, UserLogin, User, PhotoQueue, InfoUpdate, PhotoSave, Geometry
from models import UserResponse, DataResponse, PhotoDB, BoundingBox, DatosHistoricos, DatosHistoricosResponse, SidewalksDB

sidewalks_router = APIRouter(prefix="/v1/sidewalks", tags=["sidewalks"])

##################################################################################
# RUTA DE CALLES
##################################################################################

# Obtiene las calles dentro de un bounding box
@sidewalks_router.post("/data/streets")
async def get_streets(bbox: BoundingBox, user: User = Depends(get_current_active_user)) -> list[dict]:
    sw = [bbox.sw.longitude, bbox.sw.latitude]
    ne = [bbox.ne.longitude, bbox.ne.latitude]

    query = {
        "geometry.coordinates": {
            "$geoWithin": {
                "$box": [sw, ne]
            }
        }
    }
    
    streets = list(db.streets.find(query, {"_id": 0}))
    return streets

##################################################################################
# RUTA DE VEREDAS
##################################################################################

@sidewalks_router.post("/upload/sidewalks")
async def upload_sidewalks(
    image: UploadFile = File(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    date: str = Form(...),
    modo: str = Form(...),
    tipo: str = Form(...),
    user: User = Depends(get_current_active_user)):

    id = create_uuid()
    db_id = create_uuid()

    sidewalk = SidewalksDB(
        _id = db_id,
        type = "Feature",
        geometry = {
            "type": "Point",
            "coordinates": [longitude, latitude]
        },
        properties = {
            "id": db_id,
            "images": [id],
            "date": datetime.fromisoformat(date),
            "type": [tipo],
            "modo": modo,
            "user": user.username,
            "repair_at": None,
            "estado": 0,
            "observaciones": "",
            "last_update": datetime.now()
        }
    )
    
    res = procesar(sidewalk)
    
    if res:
        image = await image.read()
        image_path = f"services/imgs/{id}.jpg"
        with open(image_path, "wb") as f:
            f.write(image)
        print(f"    [API] imagen guardada con el id: {id}")
        return {" message": f"Sidewalk uploaded successfully with id: {id}"}
    else: 
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error uploading data")

@sidewalks_router.get("/data/point/sidewalks/{id}")
async def get_point(request: Request, user: User = Depends(get_current_active_user)) -> PhotoDB:
    id = request.path_params['id']
    point = db.sidewalks.find_one({"_id": id})
    if not point:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Point not found")
    return PhotoDB(**point)

@sidewalks_router.get("/data/processed_sidewalks/")
async def download_sidewalks(user: User = Depends(get_current_active_user)):
    sidewalk = list(db.sidewalks.find({}, {"_id": 0}))
    return sidewalk

@sidewalks_router.get("/data/processed_sidewalks/{tipo}")
async def download_sidewalks_type(request: Request, user: User = Depends(get_current_active_user)):
    tipo = request.path_params['tipo']
    sidewalk = list(db.sidewalks.find({"properties.type": tipo}, {"_id": 0}))
    return sidewalk

@sidewalks_router.get("/data/processed_sidewalks/{tipo}/{username}")
async def download_sidewalks_user(request: Request, user: User = Depends(get_current_active_user)):
    tipo = request.path_params['tipo']
    username = request.path_params['username']
    sidewalks = list(db.sidewalks.find({"properties.type": tipo, "properties.user": username}, {"_id": 0}))
    return sidewalks

@sidewalks_router.put("/update/sidewalks/{id}")
async def update_sidewalks(request: Request, data: InfoUpdate, user: User = Depends(get_current_active_user)):
    id = request.path_params['id']
    sidewalk = db.sidewalks.find_one({"properties.id": id})
    if not sidewalk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sidewalk not found")
    sidewalk = SidewalksDB(**sidewalk)
    collection = db['sidewalks']
    update_fields = {f"properties.{k}": v for k, v in data.model_dump().items() if v is not None}
    update_fields["properties.last_update"] = datetime.now() 
    result = collection.update_one({"properties.id": id}, {"$set": update_fields})
    return {"message": "Data updated successfully"}

@sidewalks_router.delete("/delete/sidewalks/{image_id}")
async def delete_data(request: Request, user: User = Depends(get_current_active_user)):
    image_id = request.path_params['image_id']
    punto = db.sidewalks.find_one({"_id": image_id})
    if not punto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    punto = PhotoDB(**punto)
    collection = db['sidewalks']
    result = collection.delete_one({"_id": image_id})
    if not result.deleted_count:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    return {"message": "Data deleted successfully"}
