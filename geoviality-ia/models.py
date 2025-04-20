from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class PhotoInfo(BaseModel):
    id: str
    latitude: float
    longitude: float
    date: datetime
    type: list[str]
    modo: str 
    user: str

class PhotoDB(PhotoInfo): 
    repair_at: Optional[datetime] = None
    estado: int
    observaciones: str

class PhotoSend(BaseModel):
    image: str
    id: str

# Propiedades GeoJSON
class Properties(BaseModel):
    id: str
    images: list[str]
    date: datetime
    type : list[str]
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
class GeoJson(BaseModel):
    _id: str
    type: str = "Feature"
    geometry: Geometry
    properties: Properties