from fastapi import APIRouter, Request, Depends, status
from datetime import datetime
from fastapi.exceptions import HTTPException
from typing import List
import dotenv

from .events_controllers import (
    modificar_calles,
    eliminar_de_calles,
    encontrar_calle_mas_cercana,
    normalize_types,
)
from .events_schemas import (
    InfoUpdate,
    PhotoDB,
    DataResponse,
    Geometry,
    User,
)
from .events_querys import (
    find_processed_photo_by_id,
    update_processed_photo,
    delete_processed_photo,
    list_processed_photos,
    list_processed_photos_by_date,
    find_user_by_username,
    get_current_active_user,
)

dotenv.load_dotenv()

events_router = APIRouter(prefix="/v1/events", tags=["events"])

##################################################################################
# RUTAS MODIFICACIÓN DE REGISTROS
##################################################################################

# Actualiza la información de la imagen 'image_id' en la base de datos
@events_router.put("/data/update_data/{image_id}")
async def update_data(request: Request, data: InfoUpdate, user: User = Depends(get_current_active_user)):
    image_id = request.path_params['image_id']
    raw_point = find_processed_photo_by_id(image_id)
    if not raw_point:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    punto = PhotoDB(**raw_point)
    payload = data.model_dump(exclude_none=True, by_alias=True)
    type_provided = "type" in payload
    raw_types = payload.pop("type", None) if type_provided else None
    new_types = normalize_types(raw_types) if type_provided else []
    update_fields = {f"properties.{k}": v for k, v in payload.items()}
    update_fields["properties.last_update"] = datetime.now()
    if type_provided:
        update_fields["properties.type"] = new_types
    update_result = update_processed_photo(image_id, update_fields)
    if not update_result or not update_result.matched_count:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    nuevo_estado = payload.get("estado")
    modificar_calles(
        image_id,
        punto.geometry,
        new_types if type_provided else None,
        punto.properties.type_,
        nuevo_estado,
        punto.properties.estado
    )
    return {"message": "Data updated successfully"}

# Elimina la información de la imagen 'image_id' en la base de datos
@events_router.delete("/data/delete_data/{image_id}")
async def delete_data(request: Request, user: User = Depends(get_current_active_user)):
    image_id = request.path_params['image_id']
    raw_point = find_processed_photo_by_id(image_id)
    if not raw_point:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    punto = PhotoDB(**raw_point)
    tipos = normalize_types(punto.properties.type_)
    delete_result = delete_processed_photo(image_id)
    if not delete_result or not delete_result.deleted_count:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    eliminar_de_calles(image_id, punto.geometry, tipos)
    return {"message": "Data deleted successfully"}

@events_router.get("/data/getStreetName/{lon}/{lat}", status_code=status.HTTP_200_OK)
async def getStreetName(request: Request):
    lon = float(request.path_params['lon'])
    lat = float(request.path_params['lat'])
    punto = Geometry(coordinates=[lon, lat])
    calle = encontrar_calle_mas_cercana(punto)
    if not calle or "properties" not in calle or "name" not in calle["properties"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Street not found at the specified coordinates.",
        )
    return {"street_name": calle["properties"]["name"]}


##################################################################################
# RUTAS Archivos
##################################################################################

# Obtiene información de las imágenes procesadas desde la base de datos
@events_router.get("/data/processed_info")
async def get_processed_info(user: User = Depends(get_current_active_user)) -> list[PhotoDB]:
    processed_images = list_processed_photos()
    data = DataResponse(info=processed_images)
    return data.info

# Obtiene información de las imágenes procesadas de un tipo específico desde la base de datos
@events_router.get("/data/processed_info/{type}")
async def get_processed_info_type(request: Request, user: User = Depends(get_current_active_user)) -> list[PhotoDB]:
    raw_type = request.path_params['type']
    normalized_type = raw_type.replace("-", " ") if "-" in raw_type else raw_type
    processed_images = list_processed_photos({"properties.type": normalized_type})
    data = DataResponse(info=processed_images)
    return data.info

# Obtiene información de una imagen procesada de la IA
@events_router.get("/data/point/{id}")
async def get_point(request: Request, user: User = Depends(get_current_active_user)) -> PhotoDB:
    id = request.path_params['id']
    point = find_processed_photo_by_id(id)
    if not point:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Point not found")
    return PhotoDB(**point)

@events_router.get("/data/processed_info/date/{year}/{month}")
async def get_processed_info_date(year: int, month: int, user: User = Depends(get_current_active_user)) -> List[PhotoDB]:
    year = int(year)
    month = int(month)
    start_date = datetime(year, month, 1)
    end_date = datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1)
    processed_images = list_processed_photos_by_date(start_date, end_date)
    data = DataResponse(info=processed_images)
    return data.info

# Obtiene información de las imágenes procesadas de un usuario específico desde la base de datos
@events_router.get("/data/processed_user/{username}")
async def get_processed_user(request: Request, user: User = Depends(get_current_active_user)) -> list[PhotoDB]:
    username = request.path_params['username']
    if not find_user_by_username(username):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not exists")
    processed_images = list_processed_photos({"properties.user": username})
    data = DataResponse(info=processed_images)
    return data.info

# Obtiene información de las imágenes procesadas de un usuario y tipo específico desde la base de datos
@events_router.get("/data/processed_user/{username}/{type}")
async def get_processed_user_type(request: Request, user: User = Depends(get_current_active_user)) -> list[PhotoDB]:
    username = request.path_params['username']
    if not find_user_by_username(username):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not exists")
    raw_type = request.path_params['type']
    normalized_type = raw_type.replace("-", " ") if "-" in raw_type else raw_type
    processed_images = list_processed_photos({
        "properties.user": username,
        "properties.type": normalized_type
    })
    data = DataResponse(info=processed_images)
    return data.info