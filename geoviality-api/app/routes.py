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

from database import db
from controllers import create_uuid, send_to_queue
from controllers import create_user_to_mongodb, read_user_from_mongodb, update_user_to_mongodb, delete_user_from_mongodb
from controllers import authenticate_user, create_access_token, get_current_active_user, receive_image_from_IA
from controllers import read_all_users_from_mongodb,modificar_calles , event_generator1, event_generator2 , obtener_datos_historicos, eliminar_de_calles, test, encontrar_calle_mas_cercana
from controllers import ACCESS_TOKEN_EXPIRE_MINUTES, event_queue1, event_queue2 , procesar
from models import UserCreate, UserUpdate, Token, UserSol, UserLogin, User, PhotoQueue, InfoUpdate, PhotoSave, Geometry
from models import UserResponse, DataResponse, PhotoDB, BoundingBox, DatosHistoricos, DatosHistoricosResponse, SidewalksDB

router = APIRouter()
active_connections: List[WebSocket] = []

chile_timezone = pytz.timezone('America/Santiago')

##################################################################################
# RUTAS IA
##################################################################################

# Sube una imagen a 'pre_pro' y envía la información a la cola de RabbitMQ
@router.post("/upload/image")
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

# Obtiene información de las imágenes procesadas desde la base de datos
@router.get("/data/processed_info")
async def get_processed_info(user: User = Depends(get_current_active_user)) -> list[PhotoDB]:
    processed_images = list(db.processed_geojson.find())
    data = DataResponse(info = processed_images)
    return data.info

# Obtiene información de las imágenes procesadas de un tipo específico desde la base de datos
@router.get("/data/processed_info/{type}")
async def get_processed_info_type(request: Request, user: User = Depends(get_current_active_user)) -> list[PhotoDB]:
    type = request.path_params['type']
    if "-" in type:
        type = type.replace("-", " ")
    try:
        processed_images = list(db.processed_geojson.find({"properties.type": type}))
        data = DataResponse(info = processed_images)
        return data.info
    except:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Type not found")

# Descarga la imagen 'image_id' de 'post_pro'
@router.get("/download/get_image/{image_id}")
async def download_image(request: Request, user: User = Depends(get_current_active_user)) -> FileResponse:
    image_id = request.path_params['image_id']
    file_path = os.path.join(os.getcwd(),f"services/imgs/{image_id}.jpg")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    return FileResponse(file_path)

# Obtiene información de una imagen procesada de la IA
@router.get("/data/point/{id}")
async def get_point(request: Request, user: User = Depends(get_current_active_user)) -> PhotoDB:
    id = request.path_params['id']
    point = db.processed_geojson.find_one({"_id": id})
    if not point:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Point not found")
    return PhotoDB(**point)

# Obtener una imagen procesada de la IA
@router.post("/data/processed_image")
async def get_processed_image(data: PhotoSave):
    receive_image_from_IA(data)
    photo = db.processed_geojson.find_one({"properties.images": data.id})
    if photo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
    photo = PhotoDB(**photo)
    await event_queue1.put(photo.model_dump_json())
    await event_queue2.put(photo.model_dump_json())
    return {"message": "Image received successfully"}

@router.get("/data/processed_info/date/{year}/{month}")
async def get_processed_info_date(year: int, month: int, user: User = Depends(get_current_active_user)) -> List[PhotoDB]:
    year = int(year)
    month = int(month)
    
    start_date = datetime(year, month, 1)
    end_date = datetime(year, month + 1, 1) if month < 12 else datetime(year + 1, 1, 1)

    processed_images = list(db.processed_geojson.find({
        "properties.date": {
            "$gte": start_date,
            "$lt": end_date
        }
    }))

    data = DataResponse(info=processed_images)
    return data.info

# Obtiene información de las imágenes procesadas de un usuario específico desde la base de datos
@router.get("/data/processed_user/{username}")
async def get_processed_user(request: Request, user: User = Depends(get_current_active_user)) -> list[PhotoDB]:
    username = request.path_params['username']
    usuario = db.users.find_one({"username": username})
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not exists")
    processed_images = list(db.processed_geojson.find({"properties.user": username}))
    data = DataResponse(info=processed_images)
    return data.info

# Obtiene información de las imágenes procesadas de un usuario y tipo específico desde la base de datos
@router.get("/data/processed_user/{username}/{type}")
async def get_processed_user_type(request: Request, user: User = Depends(get_current_active_user)) -> list[PhotoDB]:
    username = request.path_params['username']
    usuario = db.users.find_one({"username": username})
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not exists")
    type = request.path_params['type']
    if "-" in type:
        type = type.replace("-", " ")
    processed_images = list(db.processed_geojson.find({"properties.user": username, "properties.type": type}))
    data = DataResponse(info=processed_images)
    return data.info

##################################################################################
# RUTAS CRUD
##################################################################################

# Create User
@router.post("/user/create", status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    res = create_user_to_mongodb(user)
    if not res:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")
    return {"message": "User created successfully"}

# Read User
@router.get("/user/read/{username}")
async def read_user(request: Request, requester: User = Depends(get_current_active_user)) -> UserResponse:
    username = request.path_params['username']
    user = read_user_from_mongodb(username)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

# Update User
@router.put("/user/update/{username}")
async def update_user(request: Request ,user : UserSol, requester: User = Depends(get_current_active_user)):
    username = request.path_params['username']
    updatedUser = UserUpdate(**user.model_dump(), username=username)
    res = update_user_to_mongodb(updatedUser)
    if res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"message ": "User updated successfully"}

# Delete User
@router.delete("/user/delete/{username}")
async def delete_user(request: Request, requester: User = Depends(get_current_active_user)):
    username = request.path_params['username']
    res = delete_user_from_mongodb(username)
    if res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"message": "User deleted successfully"}

# Read All Users
@router.get("/user/read_all")
async def read_users(requester: User = Depends(get_current_active_user)) -> list[UserResponse]:
    users = read_all_users_from_mongodb()
    return users

##################################################################################
# RUTAS LOGIN
##################################################################################

# Login
@router.post("/auth/login")
async def login(userReq: OAuth2PasswordRequestForm = Depends(), tipo: str = Form(...))-> Token:
    user = authenticate_user(UserLogin(username=userReq.username,password=userReq.password))
    if not user:
        raise HTTPException(
            status_code= status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate":"Bearer"}
        )
    if user["tipo"] < int(tipo):
        raise HTTPException(
            status_code= status.HTTP_401_UNAUTHORIZED,
            detail="User not authorized",
            headers={"WWW-Authenticate":"Bearer"}
        )
    access_token_expires = timedelta(minutes = ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data= {"sub": user['username']}, expires_delta= access_token_expires)
    return Token(access_token=access_token, token_type="bearer")

# Ruta de verificación de usuario
@router.get("/users/me/")
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user

##################################################################################
# RUTAS MODIFICACIÓN DE REGISTROS
##################################################################################

# Actualiza la información de la imagen 'image_id' en la base de datos
@router.put("/data/update_data/{image_id}")
async def update_data(request: Request, data: InfoUpdate, user: User = Depends(get_current_active_user)):
    image_id = request.path_params['image_id']
    punto = db.processed_geojson.find_one({"_id": image_id})
    if not punto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    punto = PhotoDB(**punto)
    collection = db['processed_geojson']
    update_fields = {f"properties.{k}": v for k, v in data.model_dump().items() if v is not None}
    update_fields["properties.last_update"] = datetime.now() 
    tipos = [tipo.capitalize() for tipo in data.type]
    result = collection.update_one({"_id": image_id}, {"$set": update_fields})
    modificar_calles(image_id,punto.geometry, tipos, punto.type, data.estado, punto.properties.estado)
    return {"message": "Data updated successfully"}

# Elimina la información de la imagen 'image_id' en la base de datos
@router.delete("/data/delete_data/{image_id}")
async def delete_data(request: Request, user: User = Depends(get_current_active_user)):
    image_id = request.path_params['image_id']
    punto = db.processed_geojson.find_one({"_id": image_id})
    if not punto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    punto = PhotoDB(**punto)
    collection = db['processed_geojson']
    tipos = [tipo.capitalize() for tipo in collection.find_one({"_id": image_id})["properties"]["type"]]
    result = collection.delete_one({"_id": image_id})
    if not result.deleted_count:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    eliminar_de_calles(image_id, punto.geometry, tipos)
    return {"message": "Data deleted successfully"}

##################################################################################
# RUTAS DATOS HISTÓRICOS
################################################################################## 

# Obtiene los datos históricos
@router.get("/data/historical_data")
async def get_historical_data(user: User = Depends(get_current_active_user)) -> list[DatosHistoricos]:
    data = DatosHistoricosResponse(info = obtener_datos_historicos())
    return data.info


##################################################################################
# RUTA DE CALLES
##################################################################################

# Obtiene las calles dentro de un bounding box
@router.post("/data/streets")
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
# RUTA DE EVENTOS
##################################################################################

# Obtiene él último punto de la cola de eventos
@router.get("/data/events/last_point/web")
async def sse_points():
    return StreamingResponse(event_generator1(), media_type="text/event-stream")

@router.get("/data/events/last_point/movil")
async def sse_movil():
    return StreamingResponse(event_generator2(), media_type = "text/event-stream")

@router.websocket("/data/events/last_point")
async def websocket_points(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            data = await event_queue.get()
            await websocket.send_text(data)
    except WebSocketDisconnect:
        active_connections.remove(websocket)

# Prueba
@router.get("/test")
async def testing():
    return list(test())

@router.get("/data/getStreetName/{lon}/{lat}")
async def getStreetName(request: Request):
    lon = float(request.path_params['lon'])
    lat = float(request.path_params['lat'])
    punto = Geometry(coordinates = [lon, lat] )
    calle = encontrar_calle_mas_cercana(punto)
    if calle:
        try:
            nombre = calle["properties"]["name"]
            return nombre
        except: 
            return "Sin calle"
    else:
        return "Sin calle"

##################################################################################
# RUTA DE VEREDAS
##################################################################################

@router.post("/upload/sidewalks")
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

@router.get("/data/point/sidewalks/{id}")
async def get_point(request: Request, user: User = Depends(get_current_active_user)) -> PhotoDB:
    id = request.path_params['id']
    point = db.sidewalks.find_one({"_id": id})
    if not point:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Point not found")
    return PhotoDB(**point)

@router.get("/data/processed_sidewalks/")
async def download_sidewalks(user: User = Depends(get_current_active_user)):
    sidewalk = list(db.sidewalks.find({}, {"_id": 0}))
    return sidewalk

@router.get("/data/processed_sidewalks/{tipo}")
async def download_sidewalks_type(request: Request, user: User = Depends(get_current_active_user)):
    tipo = request.path_params['tipo']
    sidewalk = list(db.sidewalks.find({"properties.type": tipo}, {"_id": 0}))
    return sidewalk

@router.get("/data/processed_sidewalks/{tipo}/{username}")
async def download_sidewalks_user(request: Request, user: User = Depends(get_current_active_user)):
    tipo = request.path_params['tipo']
    username = request.path_params['username']
    sidewalks = list(db.sidewalks.find({"properties.type": tipo, "properties.user": username}, {"_id": 0}))
    return sidewalks

@router.put("/update/sidewalks/{id}")
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

@router.delete("/delete/sidewalks/{image_id}")
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

""" Cementerio:

# Elimina la imagen 'image_id' de 'pre_pro'
@router.delete("/data/delete_image/{image_id}")
async def delete_image(request: Request):
    image_id = request.path_params['image_id']
    if not os.path.exists(f"services/pre_pro/{image_id}"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    os.remove(f"services/pre_pro/{image_id}")
    return {"message": "Image deleted successfully"}

# Mueve la imagen 'image_id' desde 'pre_pro' a 'post_pro'
@router.put("/data/processed_image/{image_id}")
async def move_image(request: Request):
    images_dir = os.path.join(os.getcwd(), "services/pre_pro/")
    post_pro_dir = os.path.join(os.getcwd(), "services/post_pro/")
    image_file = request.path_params['image_id']
    src_path = os.path.join(images_dir, image_file)
    dest_path = os.path.join(post_pro_dir, image_file)
    if not os.path.exists(src_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    if not os.path.exists(post_pro_dir):
        raise HTTPException(status_code=status.HTTP_418_IM_A_TEAPOT, detail = "I'm a teapot")
    shutil.move(src_path, dest_path)
    return {"message": "Image moved successfully"}

# Obtiene las imágenes a procesar desde la base de datos
@router.get("/download/images_to_process")
async def pre_processed():
    images_dir = os.path.join(os.getcwd(), "services/pre_pro/")
    post_pro_dir = os.path.join(os.getcwd(), "services/post_pro/")
    
    if not os.path.exists(post_pro_dir):
        os.makedirs(post_pro_dir)
    
    all_files = os.listdir(images_dir)
    
    image_files = [f for f in all_files if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
    
    zip_path = os.path.join(images_dir, "images.zip")
    
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for image_file in image_files:
            zipf.write(os.path.join(images_dir, image_file), image_file)
    
    if not os.path.exists(zip_path):
        raise HTTPException(status_code=500, detail="Error creating ZIP file")
    
    def cleanup():
        os.remove(zip_path)
    
    return StreamingResponse(
        open(zip_path, 'rb'),
        media_type='application/zip',
        headers={'Content-Disposition': f'attachment; filename="images.zip"'},
        background=BackgroundTask(cleanup)
    )

    
##################################################################################
# REFRESH TOKEN
##################################################################################

@router.post("/auth/refresh")
async def refresh_token(user: User = Depends(get_current_user)):
    return 0

# Descarga la imagen 'image_id' de 'pre_pro'
@router.get("/download/get_pre_image/{image_id}")
async def download_pre_image(request: Request):
    image_id = request.path_params['image_id']
    file_path = os.path.join(os.getcwd(),f"services/pre_pro/{image_id}")
    return FileResponse(file_path)

@AuthJWT.load_config
def get_config():
    return Settings()

@router.exception_handler(AuthJWTException)
def authjwt_exception_handler(request: Request, exc: AuthJWTException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )    

"""