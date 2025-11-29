# ia_service/processing/pipeline.py

import logging
from typing import Dict, Any

from ia_service.core.config import settings
from ia_service.processing.predictor import ia_imagenes
from ia_service.services.files_service import (
    delete_image,
    get_post_image_path,
    get_base_dir,
)
from ia_service.services.api_service import send_to_API
from ia_service.domain.models import PhotoInfo, PhotoSend
from ia_service.data.queries.irregularities_queries import procesar
from ia_service.mq.publisher import publish_point

logger = logging.getLogger(__name__)


def _build_photo_info_dict(message: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extrae del mensaje los campos necesarios para PhotoInfo.
    Remueve 'image' y asegura que 'type' exista.
    """
    info = dict(message)
    info.pop("image", None)
    info.setdefault("type", [])
    return info


def process_image_message(image_path: str, message: Dict[str, Any]) -> bool:
    """
    Orquesta todo el flujo para un mensaje de la cola 'images'.

    Flujo:
      1. Ejecuta ia_imagenes (YOLO + dataset.csv + imagen procesada).
      2. Si no hay detecciones -> delete_image en 'post'.
      3. Si hay detecciones:
         - Si USE_POINTS_MS=False -> procesa en BD (procesar(PhotoInfo)).
         - Si USE_POINTS_MS=True -> publish_point(payload).
         - En ambos casos -> send_to_API(PhotoSend(image, id)).

    Retorna el mismo booleano que ia_imagenes:
      True  => no hay detecciones.
      False => sí hay detecciones.
    """
    image_id = message["id"]
    image_str = message["image"]
    filename = f"{image_id}.jpg"

    # Diccionario de metadatos para PhotoInfo / predictor
    meta_dict = _build_photo_info_dict(message)

    # Rutas para predictor
    post_path = get_post_image_path(filename)
    dataset_dir = get_base_dir()

    logger.info(
        "    - [IA] Procesando imagen '%s' mediante pipeline.", filename
    )

    # Llamada al predictor (mantiene contrato True/False)
    no_detections = ia_imagenes(
        settings.CAR_MODEL_PATH,
        settings.WALK_MODEL_PATH,
        image_path,
        post_path,
        dataset_dir,
        settings.DETECTION_CONFIDENCE,
        meta_dict,
    )

    if no_detections:
        logger.info(
            "    - [IA] Imagen '%s' sin detecciones, marcada para borrado.",
            filename,
        )
        delete_image(filename)
        return True

    # Hay detecciones
    # El predictor ya rellenó meta_dict["type"] con clases detectadas.
    # Cinturón de seguridad: garantizamos que sean strings.
    meta_dict["type"] = [str(t) for t in meta_dict.get("type", [])]

    # Construimos PhotoInfo con meta_dict (ya contiene 'type' actualizado)
    photo_info = PhotoInfo(**meta_dict)

    if settings.USE_POINTS_MS:
        # Hook futuro MS de puntos: publicamos el payload (PhotoInfo) en RabbitMQ "points"
        logger.info(
            "    - [IA] USE_POINTS_MS=True, publicando punto en cola '%s'.",
            settings.POINTS_QUEUE,
        )
        publish_point(payload=photo_info.model_dump())
    else:
        # Comportamiento actual: se usa BD directamente
        logger.info(
            "    - [IA] USE_POINTS_MS=False, procesando irregularidad en BD."
        )
        procesar(photo_info)

    # En cualquier caso, mandamos a la API el payload PhotoSend
    send_to_API(PhotoSend(image=image_str, id=image_id))

    logger.info(
        "    - [IA] Imagen '%s' procesada (detecciones presentes).", filename
    )

    return False
