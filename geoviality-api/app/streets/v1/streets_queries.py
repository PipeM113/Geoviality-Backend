"""Consultas a MongoDB para el dominio streets."""

from typing import Any, Dict, Optional

from app.core.database import db

COL_STREETS = "streets"


def insert_street_record(doc: Dict[str, Any]):
    """Inserta un documento en la colección de calles."""
    return db[COL_STREETS].insert_one(doc)


def find_nearest_street(lon: float, lat: float, max_distance: int = 30) -> Optional[Dict[str, Any]]:
    """
    Consulta geoespacial usando $near y $maxDistance para obtener la calle más cercana.
    Mantiene el mismo comportamiento del código original.
    """
    try:
        punto = {"type": "Point", "coordinates": [lon, lat]}
        calle = db[COL_STREETS].find_one(
            {
                "geometry": {
                    "$near": {
                        "$geometry": punto,
                        "$maxDistance": max_distance,
                    }
                }
            }
        )
        return calle
    except Exception as exc:  # pylint: disable=broad-exception-caught
        # Se mantiene el catch amplio por robustez en producción
        print(f"    -[API] Error al encontrar calle más cercana en MongoDB: {exc}")
        return None


def update_street(image_id: str, changes: Dict[str, Any]):
    """Actualiza un documento de calle por _id."""
    return db[COL_STREETS].update_one({"_id": image_id}, {"$set": changes})


def delete_street(image_id: str):
    """Elimina un documento de calle por _id."""
    return db[COL_STREETS].delete_one({"_id": image_id})
