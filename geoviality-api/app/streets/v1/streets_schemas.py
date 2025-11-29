"""Esquemas Pydantic del dominio streets."""

from pydantic import BaseModel, ConfigDict


class Geometry(BaseModel):
    """GeoJSON geometry genérica (permite campos adicionales)."""
    model_config = ConfigDict(extra="allow")
    type: str
    coordinates: list


class BoundingBox(BaseModel):
    """Caja de coordenadas que delimita una zona geográfica."""
    model_config = ConfigDict(extra="allow")
    north: float
    south: float
    east: float
    west: float
