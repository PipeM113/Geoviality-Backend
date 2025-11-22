from typing import Any, Dict, List, Optional
from app.core.database import db

COL = "sidewalks"

def insert_sidewalk(doc: Dict[str, Any]):
    return db[COL].insert_one(doc)

def read_sidewalk_by_id(_id: str) -> Optional[Dict[str, Any]]:
    return db[COL].find_one({"_id": _id})

def read_sidewalks(filter: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    return list(db[COL].find(filter or {}))

def update_sidewalk(_id: str, changes: Dict[str, Any]):
    return db[COL].update_one({"_id": _id}, {"$set": changes})

def delete_sidewalk(_id: str):
    return db[COL].delete_one({"_id": _id})
