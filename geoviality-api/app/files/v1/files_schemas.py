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