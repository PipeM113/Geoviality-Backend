from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class PhotoQueue(BaseModel):
    """Modelo que viaja por la cola hacia la IA.

    La imagen se envía como string (por ejemplo, bytes codificados en latin1),
    junto con la metadata necesaria.
    """
    id: str
    image: str
    latitude: float
    longitude: float
    date: datetime
    modo: str
    user: str


class PhotoSave(BaseModel):
    """Modelo que se usa para guardar imágenes en disco desde la API.

    Este modelo está pensado para el flujo que viene **desde** la IA.
    Debe ser JSON-compatible con `ia_service.domain.models.PhotoSend`:
    ambos tienen los campos `id` e `image` como string.
    """
    id: str
    image: str


class PhotoDB(BaseModel):
    """Modelo flexible para documentos de imágenes almacenadas en la BD."""
    model_config = ConfigDict(extra="allow")
    id: str


class InfoUpdate(BaseModel):
    """Payload genérico para actualizar información de una imagen en la BD."""
    model_config = ConfigDict(extra="allow")
