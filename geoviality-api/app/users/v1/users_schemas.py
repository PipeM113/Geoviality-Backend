from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List

class User(BaseModel):
    model_config = ConfigDict(extra="allow")
    username: str

class UserCreate(BaseModel):
    username: str
    password: str
    # agrega aquí los campos exactos que ya usas (email, role, etc.)

class UserUpdate(BaseModel):
    password: Optional[str] = None
    # agrega aquí campos opcionales actualizables

class UserResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    username: str

class ListUserResponse(BaseModel):
    users: List[UserResponse]
