from typing import Dict, Any
from app.core.database import db

COL_PROCESSED = "images_processed"
COL_TO_PROCESS = "images_to_process"

def insert_processed_image(doc: Dict[str, Any]):
    return db[COL_PROCESSED].insert_one(doc)

def update_processed_image(image_id: str, changes: Dict[str, Any]):
    return db[COL_PROCESSED].update_one({"_id": image_id}, {"$set": changes})

def delete_image(image_id: str):
    return db[COL_PROCESSED].delete_one({"_id": image_id})

def insert_image_to_process(doc: Dict[str, Any]):
    return db[COL_TO_PROCESS].insert_one(doc)
