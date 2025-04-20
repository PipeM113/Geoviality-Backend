import uuid
import os
import socket
import pika
import dotenv
import asyncio
from database import db
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

##################################################################################
# TOKEN FUNCS
##################################################################################

# Crea un token de acceso
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(chile_timezone) + expires_delta
    else:
        expire = datetime.now(chile_timezone) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Obtiene el usuario actual
async def get_current_user(token: Annotated[str,Depends(oauth2)]) -> User:
    credentials_exception = HTTPException( 
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except JWTClaimsError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token claims")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = get_user_from_mongodb(username=token_data.username)
    if user is None:
        raise credentials_exception
    return User(**user)

# Obtiene el usuario actual activo
async def get_current_active_user(current_user: Annotated[User,Depends(get_current_user)]) -> User:
    if current_user.disabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user

##################################################################################
# FUNCIONES PARA AUTENTICACIÓN
##################################################################################

# Lee un usuario de la base de datos
def get_user_from_mongodb(username:str) -> dict | None:
    collection = db['users']
    try:
        user = collection.find_one({"username": username})
        return user
    except PyMongoError as e:
        print(f"    -[API] Error al obtener usuario de MongoDB: {e}")
        return None
    except Exception as e:
        print(f"    -[API] Error al obtener usuario de MongoDB: {e}")
        return None

# Encripta la contraseña
def encrypt_password(password: str) -> str:
    return pwd_context.hash(password)

# Autentica al usuario
def authenticate_user(userLog: UserLogin) -> dict | bool:
    user = get_user_from_mongodb(userLog.username)
    if not user:
        return False
    if not verify_password(userLog.password, user['password']):
        return False
    return user

# Verifica la contraseña
def verify_password(password, hashed_password) -> bool:
    return pwd_context.verify(password,hashed_password)

##################################################################################
# FUNCIONES CRUD USUARIOS
##################################################################################

# Create Usuario
def create_user_to_mongodb(user : UserCreate) -> bool:
    existing_user = get_user_from_mongodb(user.username)
    if existing_user:
        return False
    collection = db['users']
    hash_password = encrypt_password(user.password)
    user_dict = user.model_dump()
    user_dict.pop('password', None)
    newUser = UserDB(**user_dict,_id = str(ObjectId()) ,password=hash_password, date_register=datetime.now(chile_timezone), disabled=False)
    try:
        result = collection.insert_one(newUser.model_dump())
        if result.inserted_id:
            return True
        return False
    except PyMongoError as e:
        print(f"    -[API] Error al crear usuario en MongoDB: {e}")
    except Exception as e:
        print(f"    -[API] Error al crear usuario en MongoDB: {e}")
        return False

# Read Usuario
def read_user_from_mongodb(username: str) -> UserResponse| None:
    collection = db['users']
    try:
        user = collection.find_one({"username": username})
        if not user:
            return None
        retUser = UserResponse(**user)
        return retUser
    except Exception as e:
        print(f"    -[API] Error al obtener usuario de MongoDB: {e}")
        return None

# Update Usuario
def update_user_to_mongodb(user: UserUpdate) -> bool:
    collection = db['users']
    if user.password is not None:
        user.password = encrypt_password(user.password)
    user_dict = user.model_dump()
    user_dict = {k: v for k, v in user_dict.items() if v is not None}
    try:
        res = collection.update_one(
            {"username": user.username},
            {"$set": user_dict}
            )
        
        if res.modified_count == 0:
            return True
        return False
    except PyMongoError as e:
        print(f"    -[API] Error al actualizar usuario en MongoDB: {e}")
        return False
    except Exception as e:
        print(f"    -[API] Error al actualizar usuario en MongoDB: {e}")
        return False

# Delete Usuario
def delete_user_from_mongodb(username : str) -> bool:
    collection = db['users']
    try:
        res = collection.delete_one({"username": username})
        if res.deleted_count == 0:
            return True
    except PyMongoError as e:
        print(f"    -[API] Error al eliminar usuario de MongoDB: {e}")
        return False
    except Exception as e:
        print(f"    -[API] Error al eliminar usuario de MongoDB: {e}")
        return False

# Read All Usuarios
def read_all_users_from_mongodb() -> list[UserResponse]:
    try:
        users = list(db.users.find())
        retUsers = ListUserResponse(info = users)
        return retUsers.info
    except PyMongoError as e:
        print(f"    -[API] Error al obtener usuarios de MongoDB: {e}")
        return []
    except Exception as e:
        print(f"    -[API] Error al obtener usuarios de MongoDB: {e}")
        return []

##################################################################################
# FUNCIONES STREETS
##################################################################################

# Encuentra la calle más cercana a un punto dado
def encontrar_calle_mas_cercana(punto: Geometry, max_distance=30) -> dict:
    """
    Encuentra la calle más cercana a un punto dado usando una consulta geoespacial.
    """
    try:
        calle = db.streets.find_one({
            "geometry": {
                "$near": {
                    "$geometry": punto.model_dump(),
                    "$maxDistance": max_distance
                }
            }
        })
        return calle
    except PyMongoError as e:
        print(f"    -[API] Error al encontrar calle más cercana en MongoDB: {e}")
        return None
    except Exception as e:
        print(f"    -[API] Error al encontrar calle más cercana en MongoDB: {e}")
        return None

# Borra los tipos anteriores de una calle
def borrar_ant_calles(id_calle: str, ant_tipos: list):
    decrementos = {f"properties.{tipo}": -1 for tipo in ant_tipos}
    try:
        db.streets.update_one(
            {"id": id_calle},
            {
                "$inc": decrementos
            }
        )
    except PyMongoError as e:
        print(f"    -[API] Error al borrar antiguos tipos de calle en MongoDB: {e}")
    except Exception as e:
        print(f"    -[API] Error al borrar antiguos tipos de calle en MongoDB: {e}")

# Modifica la calle si se modifica la info de un punto
def modificar_calles(id_imagen: str, punto: Geometry, types: list[str], ant_types: list[str], state: int, ant_state: int):
    calle = encontrar_calle_mas_cercana(punto)
    if not calle:
        return
    id_calle = calle["id"]
    ant_types = [tipo.capitalize() for tipo in ant_types]
    types = [tipo.capitalize() for tipo in types]
    if state != None and state != ant_state:
        if state == 1:
            borrar_ant_calles(id_calle, ant_types)
            db.streets.update_one(
                {"id": id_calle},
                {
                    "$pull": {"properties.images": id_imagen},
                    "$set": {"properties.last_update": datetime.now(chile_timezone)}
                }
            )
        else:
            if types != None and types != ant_types:
                borrar_ant_calles(id_calle, ant_types)
            incrementos = {f"properties.{tipo}": 1 for tipo in types}
            db.streets.update_one(
                {"id": id_calle},
                {
                    "$inc": incrementos,
                    "$push": {"properties.images": id_imagen},
                    "$set": {"properties.last_update": datetime.now(chile_timezone)}
                }
            )
    else:
        if types != None and types!=ant_types and ant_state == 0:
            borrar_ant_calles(id_calle, ant_types)
            incrementos = {f"properties.{tipo}": 1 for tipo in types}
            db.streets.update_one(
                {"id": id_calle},
                {
                    "$inc": incrementos,
                    "$push": {"properties.images": id_imagen},
                    "$set": {"properties.last_update": datetime.now(chile_timezone)}
                }
            )

# Elimina la información de un punto de las calles
def eliminar_de_calles(id_imagen:str, punto:Geometry, tipos: list):
    decrementos = {f"properties.{tipo}": -1 for tipo in tipos}
    calle = encontrar_calle_mas_cercana(punto)
    if not calle:
        return
    id_calle = calle["id"]
    db.streets.update_one(
        {"id": id_calle},
        {
            "$pull": {"properties.images": id_imagen},
            "$inc": decrementos
        }
    )

##################################################################################
# FUNCIONES DATOS HISTORICOS
##################################################################################

# Obtiene los datos históricos
def obtener_datos_historicos():
    collection = db['processed_geojson']
    pipeline = [
        {
            "$addFields": {
                "tipoCount": {"$size": "$properties.type"}
            }
        },
        {
            "$group": {
                "_id": {
                    "anio": {"$year": "$properties.date"},
                    "mes": {"$month": "$properties.date"}
                },
                "irregularidadesTotales": {"$sum": "$tipoCount"},
                "irregularidadesReparadas": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$properties.estado", 1]},
                            "$tipoCount",
                            0
                        ]
                    }
                },
                "irregularidadesPorTipo": {
                    "$push": "$properties.type"
                },
                "allCoordinates": {
                    "$push": {
                        "lat": {"$arrayElemAt": ["$geometry.coordinates", 1]},
                        "lng": {"$arrayElemAt": ["$geometry.coordinates", 0]}
                    }
                }
            }
        },
        {
            "$project": {
                "_id": 1,
                "irregularidadesTotales": 1,
                "irregularidadesReparadas": 1,
                "allCoordinates": 1,
                "irregularidadesPorTipo": {
                    "$reduce": {
                        "input": "$irregularidadesPorTipo",
                        "initialValue": [],
                        "in": {"$concatArrays": ["$$value", "$$this"]}
                    }
                }
            }
        },
        {
            "$unwind": "$irregularidadesPorTipo"
        },
        {
            "$group": {
                "_id": {
                    "anio": "$_id.anio",
                    "mes": "$_id.mes",
                    "tipo": "$irregularidadesPorTipo"
                },
                "count": {"$sum": 1},
                "irregularidadesTotales": {"$first": "$irregularidadesTotales"},
                "irregularidadesReparadas": {"$first": "$irregularidadesReparadas"},
                "allCoordinates": {"$first": "$allCoordinates"}
            }
        },
        {
            "$group": {
                "_id": {
                    "anio": "$_id.anio",
                    "mes": "$_id.mes"
                },
                "irregularidadesTotales": {"$first": "$irregularidadesTotales"},
                "irregularidadesReparadas": {"$first": "$irregularidadesReparadas"},
                "coordenadas": {"$first": "$allCoordinates"},
                "irregularidadesPorTipo": {
                    "$push": {
                        "tipo": "$_id.tipo",
                        "count": "$count"
                    }
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "anio": "$_id.anio",
                "mes": {
                    "$switch": {
                        "branches": [
                            {"case": {"$eq": ["$_id.mes", 1]}, "then": "Enero"},
                            {"case": {"$eq": ["$_id.mes", 2]}, "then": "Febrero"},
                            {"case": {"$eq": ["$_id.mes", 3]}, "then": "Marzo"},
                            {"case": {"$eq": ["$_id.mes", 4]}, "then": "Abril"},
                            {"case": {"$eq": ["$_id.mes", 5]}, "then": "Mayo"},
                            {"case": {"$eq": ["$_id.mes", 6]}, "then": "Junio"},
                            {"case": {"$eq": ["$_id.mes", 7]}, "then": "Julio"},
                            {"case": {"$eq": ["$_id.mes", 8]}, "then": "Agosto"},
                            {"case": {"$eq": ["$_id.mes", 9]}, "then": "Septiembre"},
                            {"case": {"$eq": ["$_id.mes", 10]}, "then": "Octubre"},
                            {"case": {"$eq": ["$_id.mes", 11]}, "then": "Noviembre"},
                            {"case": {"$eq": ["$_id.mes", 12]}, "then": "Diciembre"}
                        ],
                        "default": "Unknown"
                    }
                },
                "irregularidadesTotales": 1,
                "irregularidadesReparadas": 1,
                "irregularidadesPorTipo": {
                    "$arrayToObject": {
                        "$map": {
                            "input": "$irregularidadesPorTipo",
                            "as": "item",
                            "in": {"k": "$$item.tipo", "v": "$$item.count"}
                        }
                    }
                },
                "coordenadas": 1
            }
        },
        {
            "$sort": SON([("anio", 1), ("mes", 1)])
        }
    ]

    try:
        result = collection.aggregate(pipeline)
        return result
    except PyMongoError as e:
        print(f"    -[API] Error al obtener datos históricos de MongoDB: {e}")
        return None
    except Exception as e:
        print(f"    -[API] Error al obtener datos históricos de MongoDB: {e}")
        return None

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

# Función de testeo general
def test():
    return "Cris Chupalo"

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

    
""" Cementerio:

def move_image(image_filename: str) -> None:
    #mueve la imgen de services/pre_pro a services/post_pro
    pre_pro_dir = os.path.join(os.getcwd(), "services", "pre_pro")
    post_pro_dir = os.path.join(os.getcwd(), "services", "post_pro")
    image_path = os.path.join(pre_pro_dir, image_filename)
    new_image_path = os.path.join(post_pro_dir, image_filename)
    os.rename(image_path, new_image_path)
    print(f"Imagen '{image_filename}' movida de 'pre_pro' a 'post_pro'")

def delete_image(image_filename: str) -> None:
    #elimina la imagen de services/post_pro
    post_pro_dir = os.path.join(os.getcwd(), "services", "post_pro")
    image_path = os.path.join(post_pro_dir, image_filename)
    os.remove(image_path)
    print(f"Imagen '{image_filename}' eliminada de 'post_pro'")

def save_data_to_mongodb(image_filename, latitude, longitude, date, modo):
    collection = db['images_to_process']
    
    data = {
        "_id": str(ObjectId()),
        "image_filename": image_filename,
        "latitude": latitude,
        "longitude": longitude,
        "date": date,
        "modo": modo
    }
    
    result = collection.insert_one(data)
    print(f"Datos guardados en MongoDB con el ID: {result.inserted_id}")

    def create_refresh_token(data: dict):
    expire = datetime.now(chile_timezone) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def save_token_to_mongodb(token: str, username: str) -> bool:
    collection = db['tokens']
    token_data = TokenDB(token=token, username=username, created=datetime.now(chile_timezone), expires=datetime.now(chile_timezone) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    result = collection.insert_one(token_data.model_dump())
    if result.inserted_id:
        return True
    return False

def invalidate_previous_tokens(username: str) -> bool:
    collection = db['tokens']
    res = collection.delete_many({"username": username})
    if collection.count_documents({"username": username}) == 0:
        return True
    return False

"""