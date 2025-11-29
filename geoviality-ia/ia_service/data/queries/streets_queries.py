# ia_service/data/queries/streets_queries.py
from datetime import datetime
from ia_service.data.database import db
from ia_service.domain.models import Geometry
from typing import List, Dict, Any


def encontrar_calle_mas_cercana(
    punto: Geometry, max_distance: int = 30
) -> Dict[str, Any] | None:
    """
    Encuentra la calle más cercana a un punto dado usando una consulta geoespacial.
    Equivalente a la función original en funcs.py.
    """
    return db.streets.find_one(
        {
            "geometry": {
                "$near": {
                    "$geometry": punto.model_dump(),
                    "$maxDistance": max_distance,
                }
            }
        }
    )


def actualizar_calle_con_irregularidades(
    calle_id: str, id_imagen: str, tipos_irregularidades: List[str]
) -> None:
    """
    Actualiza la calle incrementando cada tipo de irregularidad proporcionado
    y agregando el id de imagen, igual que en funcs.py.
    """
    incrementos = {
        f"properties.{tipo}": 1 for tipo in tipos_irregularidades
    }

    db.streets.update_one(
        {"id": calle_id},
        {
            "$inc": incrementos,
            "$addToSet": {"properties.images": id_imagen},
            "$set": {"properties.last_update": datetime.now()},
        },
    )
