from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime

class PhotoCreate(BaseModel):
    image: Any 
    longitude: float
    latitude: float
    date: datetime

class Zip(BaseModel):
    zip_file: Any

class PhotoResponse(BaseModel):
    id: str
    image_url: str
    longitude: float
    latitude: float
    precision: int
    date: datetime
    type: int
    confidence: float