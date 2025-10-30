from .historical_models import DatosHistoricos
from mongoengine.errors import OperationError

def get_historical_data_query():
    pipeline = [
        {
            "$addFields": {
                "tipoCount": {"$size": "$properties.type"}
            }
        },
        {
            "$group": {
                "_id": {
                    "anio": {"$year": "$properties.date"},
                    "mes": {"$month": "$properties.date"}
                },
                "irregularidadesTotales": {"$sum": "$tipoCount"},
                "irregularidadesReparadas": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$properties.estado", 1]},
                            "$tipoCount",
                            0
                        ]
                    }
                },
                "irregularidadesPorTipo": {
                    "$push": "$properties.type"
                },
                "allCoordinates": {
                    "$push": {
                        "lat": {"$arrayElemAt": ["$geometry.coordinates", 1]},
                        "lng": {"$arrayElemAt": ["$geometry.coordinates", 0]}
                    }
                }
            }
        },
        {
            "$project": {
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
            }
        },
        {
            "$unwind": "$irregularidadesPorTipo"
        },
        {
            "$group": {
                "_id": {
                    "anio": "$_id.anio",
                    "mes": "$_id.mes",
                    "tipo": "$irregularidadesPorTipo"
                },
                "count": {"$sum": 1},
                "irregularidadesTotales": {"$first": "$irregularidadesTotales"},
                "irregularidadesReparadas": {"$first": "$irregularidadesReparadas"},
                "allCoordinates": {"$first": "$allCoordinates"}
            }
        },
        {
            "$group": {
                "_id": {
                    "anio": "$_id.anio",
                    "mes": "$_id.mes"
                },
                "irregularidadesTotales": {"$first": "$irregularidadesTotales"},
                "irregularidadesReparadas": {"$first": "$irregularidadesReparadas"},
                "coordenadas": {"$first": "$allCoordinates"},
                "irregularidadesPorTipo": {
                    "$push": {
                        "tipo": "$_id.tipo",
                        "count": "$count"
                    }
                }
            }
        },
        {
            "$project": {
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
            }
        },
        {
            "$sort": {"anio": 1, "mes": 1}
        }
    ]
    try:
        result = DatosHistoricos.objects.aggregate(pipeline)
        return list(result)
    except OperationError as e:
        print(f"    -[API] Error al obtener datos históricos de MongoDB: {e}")
        return None
    except Exception as e:
        print(f"    -[API] Error al obtener datos históricos de MongoDB: {e}")
        return None
