# ia_service/mq/publisher.py
import json
import logging
import pika

from ia_service.core.config import settings

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


def publish_point(payload: dict) -> None:
    """
    Publica un mensaje en la cola de RabbitMQ 'points' (o la configurada en settings.POINTS_QUEUE).
    Este es el hook para el futuro microservicio de puntos.
    """
    connection = _build_connection()
    try:
        channel = connection.channel()
        channel.queue_declare(queue=settings.POINTS_QUEUE, durable=True)
        channel.basic_publish(
            exchange="",
            routing_key=settings.POINTS_QUEUE,
            body=json.dumps(payload),
            properties=pika.BasicProperties(delivery_mode=2),
        )
        logger.info(
            "    - [IA] Punto publicado en cola '%s'.", settings.POINTS_QUEUE
        )
    finally:
        connection.close()
