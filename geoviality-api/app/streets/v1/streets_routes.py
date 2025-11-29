"""Rutas del dominio streets (prefix='/v1/streets')."""

from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.v1.auth_controllers import get_current_active_user
from app.streets.v1.streets_schemas import BoundingBox
from app.streets.v1.streets_controllers import (
    create_street_record,
    get_street_name_from_coords,
    update_street_record,
    delete_street_record,
)

router = APIRouter(
    prefix="/v1/streets",
    tags=["streets"],
)


@router.post("/data")
async def create_streets(
    box: BoundingBox,
    _=Depends(get_current_active_user),
) -> dict:
    """Crea un registro de calles a partir de un BoundingBox (requiere autenticación)."""
    ok = create_street_record(box)
    return {"created": ok}


@router.get("/getStreetName/{lon}/{lat}")
async def get_street_name(
    lon: float,
    lat: float,
    _=Depends(get_current_active_user),
) -> Dict[str, Any]:
    """Devuelve la información de la calle más cercana a lon/lat (requiere autenticación)."""
    return get_street_name_from_coords(lon, lat)


@router.put("/processed_image/{image_id}")
async def update_processed_image(
    image_id: str,
    changes: Dict[str, Any],
    _=Depends(get_current_active_user),
) -> dict:
    """Actualiza un registro de calle procesada por id (requiere autenticación)."""
    ok = update_street_record(image_id, changes)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found or unchanged",
        )
    return {"updated": True}


@router.delete("/delete_data/{image_id}")
async def delete_processed_image(
    image_id: str,
    _=Depends(get_current_active_user),
) -> dict:
    """Elimina un registro de calle procesada por id (requiere autenticación)."""
    ok = delete_street_record(image_id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found",
        )
    return {"deleted": True}
