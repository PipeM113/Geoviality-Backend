# app/historical/v1/historical_queries.py
from typing import Any, Dict, List
from datetime import datetime
from bson import SON
from app.core.database import db

COL_HIST = "processed_geojson"

def find_historical(filter: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    return list(db[COL_HIST].find(filter or {}))

def find_historical_by_id(_id: str) -> Dict[str, Any] | None:
    return db[COL_HIST].find_one({"_id": _id})

def find_processed_info(filter: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    """
    Comportamiento original:
      - sin filtro -> todos
      - {"type": <tipo>} -> filtra por properties.type
      - {"properties.date": {"$gte": start, "$lt": end}} -> rango de fechas
      - filtro genérico -> find(filtro)
    """
    if not filter:
        return list(db[COL_HIST].find())

    if "type" in filter:
        return list(db[COL_HIST].find({"properties.type": filter["type"]}))

    if "properties.date" in filter:
        return list(db[COL_HIST].find({"properties.date": filter["properties.date"]}))

    return list(db[COL_HIST].find(filter))

def find_processed_user(username: str, type_: str | None = None) -> List[Dict[str, Any]]:
    """
    Consulta por usuario (y opcionalmente por tipo) en processed_geojson,
    como en tu implementación original.
    """
    q: Dict[str, Any] = {"properties.username": username}
    if type_:
        q["properties.type"] = type_
    return list(db[COL_HIST].find(q))

def find_historical_aggregated() -> List[Dict[str, Any]]:
    """
    Pipeline agregado (equivalente a tu obtener_datos_historicos).
    Ajusta nombres si tu colección/campos difieren.
    """
    pipeline = [
        {"$addFields": {"tipoCount": {"$size": "$properties.type"}}},
        {"$group": {
            "_id": {
                "anio": {"$year": "$properties.date"},
                "mes": {"$month": "$properties.date"}
            },
            "irregularidadesTotales": {"$sum": "$tipoCount"},
            "irregularidadesReparadas": {"$sum": {
                "$cond": [{"$eq": ["$properties.estado", 1]}, "$tipoCount", 0]
            }},
            "irregularidadesPorTipo": {"$push": "$properties.type"},
            "allCoordinates": {"$push": {
                "lat": {"$arrayElemAt": ["$geometry.coordinates", 1]},
                "lng": {"$arrayElemAt": ["$geometry.coordinates", 0]}
            }}
        }},
        {"$project": {
            "_id": 1,
            "irregularidadesTotales": 1,
            "irregularidadesReparadas": 1,
            "allCoordinates": 1,
            "irregularidadesPorTipo": {
                "$reduce": {
                    "input": "$irregularidadesPorTipo",
                    "initialValue": [],
                    "in": {"$concatArrays": ["$$value", "$$this"]}
                }
            }
        }},
        {"$unwind": "$irregularidadesPorTipo"},
        {"$group": {
            "_id": {
                "anio": "$_id.anio",
                "mes": "$_id.mes",
                "tipo": "$irregularidadesPorTipo"
            },
            "count": {"$sum": 1},
            "irregularidadesTotales": {"$first": "$irregularidadesTotales"},
            "irregularidadesReparadas": {"$first": "$irregularidadesReparadas"},
            "allCoordinates": {"$first": "$allCoordinates"}
        }},
        {"$group": {
            "_id": {"anio": "$_id.anio", "mes": "$_id.mes"},
            "irregularidadesTotales": {"$first": "$irregularidadesTotales"},
            "irregularidadesReparadas": {"$first": "$irregularidadesReparadas"},
            "coordenadas": {"$first": "$allCoordinates"},
            "irregularidadesPorTipo": {"$push": {"tipo": "$_id.tipo", "count": "$count"}}
        }},
        {"$project": {
            "_id": 0,
            "anio": "$_id.anio",
            "mes": {
                "$switch": {
                    "branches": [
                        {"case": {"$eq": ["$_id.mes", 1]}, "then": "Enero"},
                        {"case": {"$eq": ["$_id.mes", 2]}, "then": "Febrero"},
                        {"case": {"$eq": ["$_id.mes", 3]}, "then": "Marzo"},
                        {"case": {"$eq": ["$_id.mes", 4]}, "then": "Abril"},
                        {"case": {"$eq": ["$_id.mes", 5]}, "then": "Mayo"},
                        {"case": {"$eq": ["$_id.mes", 6]}, "then": "Junio"},
                        {"case": {"$eq": ["$_id.mes", 7]}, "then": "Julio"},
                        {"case": {"$eq": ["$_id.mes", 8]}, "then": "Agosto"},
                        {"case": {"$eq": ["$_id.mes", 9]}, "then": "Septiembre"},
                        {"case": {"$eq": ["$_id.mes", 10]}, "then": "Octubre"},
                        {"case": {"$eq": ["$_id.mes", 11]}, "then": "Noviembre"},
                        {"case": {"$eq": ["$_id.mes", 12]}, "then": "Diciembre"}
                    ],
                    "default": "Unknown"
                }
            },
            "irregularidadesTotales": 1,
            "irregularidadesReparadas": 1,
            "irregularidadesPorTipo": {
                "$arrayToObject": {
                    "$map": {
                        "input": "$irregularidadesPorTipo",
                        "as": "item",
                        "in": {"k": "$$item.tipo", "v": "$$item.count"}
                    }
                }
            },
            "coordenadas": 1
        }},
        {"$sort": SON([("anio", 1), ("mes", 1)])}
    ]
    return list(db[COL_HIST].aggregate(pipeline))
