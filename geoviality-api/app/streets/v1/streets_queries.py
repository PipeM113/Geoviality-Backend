# app/streets/v1/streets_queries.py
from typing import Any, Dict, Optional
from app.core.database import db

COL_STREETS = "streets"

def insert_street_record(doc: Dict[str, Any]):
    return db[COL_STREETS].insert_one(doc)

def find_nearest_street(lon: float, lat: float, max_distance: int = 30) -> Optional[Dict[str, Any]]:
    """
    Consulta geoespacial usando $near y $maxDistance para obtener la calle más cercana.
    """
    try:
        punto = {"type": "Point", "coordinates": [lon, lat]}
        calle = db[COL_STREETS].find_one({
            "geometry": {
                "$near": {
                    "$geometry": punto,
                    "$maxDistance": max_distance
                }
            }
        })
        return calle
    except Exception as e:
        print(f"    -[API] Error al encontrar calle más cercana en MongoDB: {e}")
        return None

def update_street(image_id: str, changes: Dict[str, Any]):
    return db[COL_STREETS].update_one({"_id": image_id}, {"$set": changes})

def delete_street(image_id: str):
    return db[COL_STREETS].delete_one({"_id": image_id})
