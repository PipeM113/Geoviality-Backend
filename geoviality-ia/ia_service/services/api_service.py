# ia_service/services/api_service.py
import logging
import time

import requests

from ia_service.core.config import settings
from ia_service.domain.models import PhotoSend

logger = logging.getLogger(__name__)


def send_to_API(data: PhotoSend) -> None:
    """Envía los datos de la imagen procesada a la API.

    Realiza un POST `/v1/files/from-ia` (lado API) con reintentos,
    manteniendo la misma lógica básica que la versión anterior.
    """
    retries = 0
    max_retries = 3

    while retries < max_retries:
        try:
            request_url = f"{settings.API_BASE_URL}/v1/files/from-ia"
            response = requests.post(request_url, json=data.model_dump())
            response.raise_for_status()
            logger.info("    - [IA] Imagen '%s' enviada a la API.", data.id)
            break
        except requests.exceptions.RequestException as e:
            retries += 1
            logger.warning(
                "    - [IA] Error al enviar la imagen '%s' a la API: %s "
                "(intento %d/%d)",
                data.id,
                e,
                retries,
                max_retries,
            )
            if retries < max_retries:
                logger.info("    - [IA] Reintentando en 5 segundos...")
                time.sleep(5)

    if retries == max_retries:
        logger.error("    - [IA] No se pudo enviar la imagen '%s' a la API.", data.id)
