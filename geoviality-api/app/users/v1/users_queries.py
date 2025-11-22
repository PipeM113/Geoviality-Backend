from typing import Optional, Dict, Any, List
from app.core.database import db

COL = "users"

def create_user(doc: Dict[str, Any]):
    return db[COL].insert_one(doc)

def read_user(username: str) -> Optional[Dict[str, Any]]:
    return db[COL].find_one({"username": username})

def update_user(username: str, changes: Dict[str, Any]):
    return db[COL].update_one({"username": username}, {"$set": changes})

def delete_user(username: str):
    return db[COL].delete_one({"username": username})

def read_all_users() -> List[Dict[str, Any]]:
    return list(db[COL].find({}))
