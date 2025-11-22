from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any

from app.auth.v1.auth_controllers import get_current_active_user
from app.sidewalks.v1.sidewalks_schemas import SidewalksDB
from app.sidewalks.v1.sidewalks_controllers import (
    upload_sidewalk_to_mongodb, get_sidewalk_point, get_processed_sidewalks,
    update_sidewalk_info, delete_sidewalk_info
)

router = APIRouter(
    prefix="/v1/sidewalks",
    tags=["sidewalks"],
)

@router.post("/upload")
async def upload_sidewalks(payload: SidewalksDB, _=Depends(get_current_active_user)):
    return upload_sidewalk_to_mongodb(payload)

@router.get("/data/point/{id}")
async def read_point_sidewalks(id: str, _=Depends(get_current_active_user)):
    return get_sidewalk_point(id)

@router.get("/data/processed/")
async def read_processed_sidewalks(_=Depends(get_current_active_user)):
    return get_processed_sidewalks()

@router.get("/data/processed/{tipo}")
async def read_processed_sidewalks_tipo(tipo: str, _=Depends(get_current_active_user)):
    return get_processed_sidewalks({"tipo": tipo})

@router.get("/data/processed/{tipo}/{username}")
async def read_processed_sidewalks_tipo_user(tipo: str, username: str, _=Depends(get_current_active_user)):
    return get_processed_sidewalks({"tipo": tipo, "username": username})

@router.put("/update/{id}")
async def update_sidewalks(id: str, changes: Dict[str, Any], _=Depends(get_current_active_user)):
    ok = update_sidewalk_info(id, changes)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found or unchanged")
    return {"updated": True}

@router.delete("/delete/{image_id}")
async def delete_sidewalks(image_id: str, _=Depends(get_current_active_user)):
    ok = delete_sidewalk_info(image_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return {"deleted": True}
