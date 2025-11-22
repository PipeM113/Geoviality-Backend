from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Any
from datetime import datetime

class PhotoQueue(BaseModel):
    id: str
    image: str
    latitude: float
    longitude: float
    date: datetime
    modo: str
    user: str

class PhotoSave(BaseModel):
    id: str
    image: bytes

class PhotoDB(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str

class InfoUpdate(BaseModel):
    model_config = ConfigDict(extra="allow")
