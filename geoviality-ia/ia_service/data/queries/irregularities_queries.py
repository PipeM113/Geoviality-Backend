# ia_service/data/queries/irregularities_queries.py
from datetime import datetime
import uuid
from ia_service.data.database import db
from ia_service.domain.models import (
    PhotoInfo,
    PhotoDB,
    GeoJson,
    Geometry,
)
from ia_service.data.queries.streets_queries import (
    encontrar_calle_mas_cercana,
    actualizar_calle_con_irregularidades,
)
import logging

logger = logging.getLogger(__name__)


def save_data_to_mongodb(photo_info: PhotoInfo) -> GeoJson:
    """
    Guarda los datos de la imagen como GeoJSON en la colección 'processed_geojson'.
    Equivalente a la función original save_data_to_mongodb.
    """
    collection = db["processed_geojson"]

    data = PhotoDB(
        **photo_info.model_dump(),
        repair_at=None,
        estado=0,
        observaciones="Sin Observaciones",
    )
    irregularidad = geoJson(data)

    try:
        result = collection.insert_one(irregularidad)
        logger.info(
            "    - [IA] Imagen '%s' guardada en 'processed_geojson' con el ID: %s.",
            photo_info.id,
            result.inserted_id,
        )
    except Exception as e:  # noqa: BLE001
        logger.warning(
            "    - [IA] Datos duplicados de la imagen '%s' en la BD, error: %s",
            photo_info.id,
            e,
        )

    return GeoJson(**irregularidad)


def actualizar_foto(foto: GeoJson, id_imagen: str) -> None:
    """
    Actualiza la foto en la BD 'processed_geojson' agregando el id de la imagen
    a la lista de 'properties.images' y actualizando 'last_update'.
    """
    try:
        db.processed_geojson.update_one(
            {"_id": foto.properties.id},
            {
                "$addToSet": {"properties.images": id_imagen},
                "$set": {"properties.last_update": datetime.now()},
            },
        )
        logger.info(
            "    - [IA] Foto '%s' actualizada con la imagen '%s'.",
            foto.properties.id,
            id_imagen,
        )
    except Exception as e:  # noqa: BLE001
        logger.error(
            "    - [IA] Error al actualizar la foto '%s': %s",
            foto.properties.id,
            e,
        )


def irregularidad_cercana(
    punto: Geometry, max_distance: int = 10
) -> GeoJson | None:
    """
    Encuentra la irregularidad más cercana a un punto dado usando una consulta geoespacial.
    """
    try:
        doc = db.processed_geojson.find_one(
            {
                "geometry": {
                    "$near": {
                        "$geometry": punto.model_dump(),
                        "$maxDistance": max_distance,
                    }
                }
            }
        )
        if not doc:
            return None
        return GeoJson(**doc)
    except Exception as e:  # noqa: BLE001
        logger.error("    - [IA] Error al buscar irregularidad cercana: %s", e)
        return None


def geoJson(data: PhotoDB) -> dict:
    """
    Construye un documento GeoJSON a partir de un PhotoDB,
    igual que la función geoJson original.
    """
    properties: dict = {}
    item = data.model_dump()
    item["_id"] = str(uuid.uuid4())
    item["images"] = [item["id"]]
    item["id"] = item["_id"]

    for key, value in item.items():
        if key not in ("longitude", "latitude", "_id"):
            properties[key] = value

    properties["last_update"] = datetime.now()

    geojson = {
        "_id": item["_id"],
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [item["longitude"], item["latitude"]],
        },
        "properties": properties,
    }
    return geojson


def procesar(info: PhotoInfo) -> None:
    """
    Equivalente a funcs.procesar(info):
    - Busca irregularidad cercana.
    - Si existe, actualiza la foto existente.
    - Si no existe, guarda una nueva en 'processed_geojson' y procesa la calle.
    """
    irr = irregularidad_cercana(
        Geometry(coordinates=[info.longitude, info.latitude])
    )

    if irr:
        logger.info(
            "    - [IA] Irregularidad cercana a la imagen '%s' encontrada.",
            info.id,
        )
        actualizar_foto(irr, info.id)
    else:
        logger.info(
            "    - [IA] No se encontró una irregularidad cercana a la imagen '%s'.",
            info.id,
        )
        geo = save_data_to_mongodb(info)
        procesar_irregularidad(geo)


def procesar_irregularidad(irregularidad: GeoJson) -> None:
    """
    Procesa una nueva irregularidad:
    - Encuentra la calle más cercana.
    - Actualiza la calle con los tipos de irregularidad detectados.
    """
    punto = irregularidad.geometry
    tipos_irregularidades = [
        tipo.capitalize() for tipo in irregularidad.properties.type
    ]

    calle = encontrar_calle_mas_cercana(punto)

    if calle:
        calle_id = calle["id"]
        actualizar_calle_con_irregularidades(
            calle_id, irregularidad.properties.id, tipos_irregularidades
        )
        logger.info(
            "    - [IA] Irregularidad procesada en la calle '%s'.", calle_id
        )
    else:
        logger.info(
            "    - [IA] No se encontró una calle cercana a la irregularidad."
        )
