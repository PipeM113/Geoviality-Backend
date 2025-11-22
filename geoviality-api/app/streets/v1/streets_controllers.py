from typing import Dict, Any, Optional
from fastapi import HTTPException, status

from app.streets.v1.streets_schemas import BoundingBox
from app.streets.v1.streets_queries import (
    insert_street_record, find_nearest_street, update_street, delete_street
)

def create_street_record(box: BoundingBox) -> bool:
    res = insert_street_record(box.model_dump())
    return bool(res.inserted_id)

def get_street_name_from_coords(lon: float, lat: float) -> Dict[str, Any]:
    doc = find_nearest_street(lon, lat)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Street not found")
    return doc

def update_street_record(image_id: str, changes: Dict[str, Any]) -> bool:
    res = update_street(image_id, changes)
    return res.modified_count > 0

def delete_street_record(image_id: str) -> bool:
    res = delete_street(image_id)
    return res.deleted_count > 0
