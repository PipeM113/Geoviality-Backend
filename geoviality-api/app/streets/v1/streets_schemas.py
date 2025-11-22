from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List

class Geometry(BaseModel):
    model_config = ConfigDict(extra="allow")
    type: str
    coordinates: list

class BoundingBox(BaseModel):
    model_config = ConfigDict(extra="allow")
    north: float
    south: float
    east: float
    west: float
