from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


##################################################################################
# MODELOS PARA FOTOS
##################################################################################

# Modelo para el envío a la cola de mensajes
class PhotoQueue(BaseModel):
    id: str
    image: str
    latitude: float
    longitude: float
    date: datetime
    modo: str
    user: str

# Modelo para recibir la foto de la IA
class PhotoSave(BaseModel):
    image: str
    id: str

# Propiedades GeoJSON
class Properties(BaseModel):
    id: str
    images: list[str]
    date: datetime
    type : list[str]|str
    modo: str
    user: str
    repair_at: Optional[datetime] = None
    estado: int
    observaciones: str
    last_update: datetime

# Geometry GeoJSON
class Geometry(BaseModel):
    type: str = "Point"
    coordinates: list[float]

# GeoJSON
class PhotoDB(BaseModel):
    _id: str
    type: str = "Feature"
    geometry: Geometry
    properties: Properties

# Respuesta para los get data
class DataResponse(BaseModel):
    info: list[PhotoDB]

# Modelo para la vareda
class SidewalksDB(BaseModel):
    _id: str
    type: str = "Feature"
    geometry: Geometry
    properties: Properties

##################################################################################
# MODELOS PARA USUARIOS
##################################################################################

# Modelo de usuario
class User(BaseModel):
    username: str
    email: str
    nombre: str
    apellido: str
    date_register: datetime
    disabled: bool
    tipo: int # 0:Usuario, 1:Analista, 2:Administrador

# Modelo de usuario en la base de datos
class UserDB(User):
    _id: str
    password: str

# Modelo de usuario de respuesta para read
class UserResponse(BaseModel):
    username: str
    email: str
    nombre: str
    apellido: str
    date_register: datetime
    disabled: bool
    tipo: int

# Modelo de usuario de respuesta para listas de usuarios
class ListUserResponse(BaseModel):
    info: list[UserResponse]

# Modelo de usuario para login
class UserLogin(BaseModel):
    username: str
    password: str

# Modelo de usuario para registro
class UserCreate(BaseModel):
    username: str
    email: str
    nombre: str
    apellido: str
    password: str
    tipo: int

# Modelo de usuario para actualización
class UserSol(BaseModel):
    email: Optional[str]=None
    nombre: Optional[str]=None
    apellido: Optional[str]=None
    password: Optional[str]=None
    tipo: Optional[int]=None

# Modelo de usuario para actualización
class UserUpdate(UserSol):
    username: str

##################################################################################
# MODELOS PARA AUTENTICACIÓN
##################################################################################

# Modelo de Token
class Token(BaseModel):
    access_token : str
    token_type: str

# Modelo de TokenData (lo que lleva el token)
class TokenData(BaseModel):
    username: str | None = None

##################################################################################
# MODELOS PARA INFO
##################################################################################

# Modelo de para modificar registros
class InfoUpdate(BaseModel):
    type: Optional[list[str]]|str = None
    repair_at: Optional[datetime] = None
    estado: Optional[int] = None
    observaciones: Optional[str] = None

# Modelo para la coordenada
class Coordinate(BaseModel):
    latitude: float
    longitude: float

# Modelo para la bounding box
class BoundingBox(BaseModel):
    sw : Coordinate
    ne : Coordinate

##################################################################################
# MODELOS PARA DATOS HISTORICOS
##################################################################################

# Modelo para los tipos de irregularidades
class IrregularidadesPorTipo(BaseModel):
    hoyo: Optional[int] = 0
    grieta: Optional[int] = 0
    cocodrilo: Optional[int] = 0
    hoyo_con_agua: Optional[int] = Field(0, alias="hoyo con agua")
    longitudinal: Optional[int] = 0
    transversal: Optional[int] = 0
    lomo_de_toro: Optional[int] = Field(0, alias="lomo de toro")

# Modelo para las coordenadas de los puntos
class Coordenadas(BaseModel):
    lat: float
    lng: float

# Modelo para los datos históricos
class DatosHistoricos(BaseModel):
    anio: int 
    mes: str 
    irregularidadesTotales: int
    irregularidadesReparadas: int
    irregularidadesPorTipo: IrregularidadesPorTipo
    coordenadas : list[Coordenadas]

# Modelo para la respuesta de los datos históricos
class DatosHistoricosResponse(BaseModel):
    info: list[DatosHistoricos]