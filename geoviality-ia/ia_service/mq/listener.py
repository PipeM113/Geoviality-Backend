# ia_service/mq/listener.py
import json
import time
import logging
import pika

from ia_service.core.config import settings
from ia_service.processing.pipeline import process_image_message
from ia_service.services.files_service import get_pre_image_path

logger = logging.getLogger(__name__)


def _build_connection() -> pika.BlockingConnection:
    params = pika.ConnectionParameters(
        host=settings.RABBITMQ_HOST,
        port=settings.RABBITMQ_PORT,
    )
    if settings.RABBITMQ_USER:
        params = pika.ConnectionParameters(
            host=settings.RABBITMQ_HOST,
            port=settings.RABBITMQ_PORT,
            credentials=pika.PlainCredentials(
                settings.RABBITMQ_USER,
                settings.RABBITMQ_PASSWORD or "",
            ),
        )
    return pika.BlockingConnection(params)


def start_listener() -> None:
    """
    Consumer de la cola 'images'.
    Conserva el flujo observable:
      - Recibe mensaje.
      - Escribe imagen en imgs/pre.
      - Llama al pipeline para procesar.
      - Ack del mensaje.
    """
    logger.info("    - [IA] Iniciando conexión a cola RabbitMQ...")

    connection = None
    while connection is None:
        try:
            connection = _build_connection()
            logger.info("    - [IA] Conexión a cola Rabbit exitosa.")
        except pika.exceptions.AMQPConnectionError:
            logger.warning(
                "    - [IA] No se pudo conectar a RabbitMQ, reintentando en 5 segundos..."
            )
            time.sleep(5)

    channel = connection.channel()
    channel.queue_declare(queue="images", durable=True)
    logger.info(
        "    - [IA] Esperando mensajes en cola 'images', para salir presione CTRL+C."
    )

    def callback(ch, method, properties, body) -> None:  # type: ignore[override]
        logger.info("    - [IA] Imagen recibida desde RabbitMQ.")
        try:
            data = json.loads(body)
            logger.info("    - [IA] Claves del mensaje: %s", list(data.keys()))
            image_str = data["image"]
            image_id = data["id"]
            image_filename = f"{image_id}.jpg"

            path = get_pre_image_path(image_filename)
            with open(path, "wb") as f:
                # Mantener la codificación original (latin1)
                f.write(image_str.encode("latin1"))

            logger.info(
                "    - [IA] Imagen '%s' guardada en 'pre' y empezando a procesar.",
                image_filename,
            )

            process_image_message(path, data)

        except Exception as e:  # noqa: BLE001
            logger.exception("    - [IA] Error procesando mensaje: %s", e)
            # Mantener la semántica simple: igual hacemos ACK para evitar loops infinitos
        finally:
            ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue="images", on_message_callback=callback)
    channel.start_consuming()
