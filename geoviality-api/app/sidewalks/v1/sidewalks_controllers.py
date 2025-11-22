from typing import Dict, Any, List
from fastapi import HTTPException, status
from app.sidewalks.v1.sidewalks_schemas import SidewalksDB
from app.sidewalks.v1.sidewalks_queries import (
    insert_sidewalk, read_sidewalk_by_id, read_sidewalks, update_sidewalk, delete_sidewalk
)

def upload_sidewalk_to_mongodb(payload: SidewalksDB) -> dict:
    res = insert_sidewalk(payload.model_dump())
    return {"inserted_id": str(res.inserted_id)}

def get_sidewalk_point(_id: str) -> dict:
    doc = read_sidewalk_by_id(_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sidewalk not found")
    return doc

def get_processed_sidewalks(filter: Dict[str, Any] | None = None) -> list[dict]:
    return read_sidewalks(filter)

def update_sidewalk_info(_id: str, changes: Dict[str, Any]) -> bool:
    res = update_sidewalk(_id, changes)
    return res.modified_count > 0

def delete_sidewalk_info(image_id: str) -> bool:
    res = delete_sidewalk(image_id)
    return res.deleted_count > 0
