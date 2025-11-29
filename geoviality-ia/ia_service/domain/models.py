# ia_service/domain/models.py
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class PhotoInfo(BaseModel):
    id: str
    latitude: float
    longitude: float
    date: datetime
    type: List[str]
    modo: str
    user: str


class PhotoDB(PhotoInfo):
    repair_at: Optional[datetime] = None
    estado: int
    observaciones: str


class PhotoSend(BaseModel):
    """Payload mínimo que la IA envía a la API.

    Debe ser compatible con el modelo PhotoSave de la API:
    mismo JSON: {"id": str, "image": str}.
    El campo `image` es la imagen procesada codificada como string
    (ej. bytes codificados con latin1 o base64, según tu pipeline).
    """
    id: str
    image: str


# Propiedades GeoJSON
class Properties(BaseModel):
    id: str
    images: List[str]
    date: datetime
    type: List[str]
    modo: str
    user: str
    repair_at: Optional[datetime] = None
    estado: int
    observaciones: str
    last_update: datetime


# Geometry GeoJSON
class Geometry(BaseModel):
    type: str = "Point"
    coordinates: List[float]


# GeoJSON
class GeoJson(BaseModel):
    _id: str
    type: str = "Feature"
    geometry: Geometry
    properties: Properties
