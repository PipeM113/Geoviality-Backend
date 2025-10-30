from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

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