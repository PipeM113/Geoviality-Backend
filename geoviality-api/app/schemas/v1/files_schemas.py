from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

##################################################################################
# MODELOS PARA FOTOS
##################################################################################

class PhotoQueue(BaseModel):
    id: str = Field(..., description="Identificador único de la imagen.")
    image: str = Field(..., description="Imagen codificada en latin1.")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitud en grados decimales.")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitud en grados decimales.")
    date: datetime = Field(..., description="Fecha de captura en formato ISO 8601.")
    modo: str = Field(..., min_length=1, description="Modo de captura reportado.")
    user: str = Field(..., min_length=1, description="Usuario que sube la imagen.")

class PhotoSave(BaseModel):
    image: str = Field(..., description="Imagen procesada codificada en latin1.")
    id: str = Field(..., description="Identificador asociado a la imagen procesada.")

class PhotoProperties(BaseModel):
    model_config = ConfigDict(extra="allow")
    images: list[str] | None = None
    user: str | None = None
    type: str | None = None
    date: datetime | None = None

class PhotoGeometry(BaseModel):
    model_config = ConfigDict(extra="allow")
    type: str | None = None
    coordinates: list | None = None

class PhotoProcessed(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")
    id: str = Field(alias="_id")
    properties: PhotoProperties = Field(default_factory=PhotoProperties)
    geometry: PhotoGeometry | None = None
