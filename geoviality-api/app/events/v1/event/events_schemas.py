from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
from typing import Optional

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    is_active: bool = True
    role: str

# Propiedades GeoJSON
class Properties(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    images: list[str] = Field(default_factory=list)
    date: datetime
    type_: list[str] = Field(default_factory=list, alias="type")
    modo: str
    user: str
    repair_at: Optional[datetime] = None
    estado: int
    observaciones: str
    last_update: datetime

    @field_validator("type_", mode="before")
    def _normalize_type(cls, value):
        if value is None:
            return []
        if isinstance(value, str):
            value = [value]
        return [str(item).strip() for item in value if str(item).strip()]

# Geometry GeoJSON
class Geometry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    type_: str = Field(default="Point", alias="type")
    coordinates: list[float]

    @field_validator("coordinates")
    def _validate_coordinates(cls, value):
        if len(value) < 2:
            raise ValueError("coordinates must contain at least two values")
        return value[:2]

# GeoJSON
class PhotoDB(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    _id: str
    type_: str = Field(default="Feature", alias="type")
    geometry: Geometry
    properties: Properties

# Respuesta para los get data
class DataResponse(BaseModel):
    info: list[PhotoDB]

# Modelo para la vareda
class SidewalksDB(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    _id: str
    type_: str = Field(default="Feature", alias="type")
    geometry: Geometry
    properties: Properties

##################################################################################
# MODELOS PARA INFO
##################################################################################

# Modelo de para modificar registros
class InfoUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    type_: Optional[list[str]] = Field(default=None, alias="type")
    repair_at: Optional[datetime] = None
    estado: Optional[int] = None
    observaciones: Optional[str] = None

    @field_validator("type_", mode="before")
    def _normalize_update_type(cls, value):
        if value is None:
            return None
        if isinstance(value, str):
            value = [value]
        return [str(item).strip() for item in value if str(item).strip()]

# Modelo para la coordenada
class Coordinate(BaseModel):
    latitude: float
    longitude: float

# Modelo para la bounding box
class BoundingBox(BaseModel):
    sw : Coordinate
    ne : Coordinate
