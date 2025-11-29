import os
import uuid

import pika
from fastapi import HTTPException, status
from pika.exceptions import AMQPError

from app.core.config import RABBITMQ_HOST, RABBITMQ_QUEUE_IMAGES, RABBITMQ_PORT
from app.core.utils import create_directories
from app.files.v1.files_schemas import PhotoQueue, PhotoSave


def send_to_queue(data: PhotoQueue) -> bool:
    """Envía un mensaje a la cola de RabbitMQ con la foto original.

    Retorna `True` si el mensaje se publica correctamente, `False` en caso contrario.
    """
    message = data.model_dump_json()
    try:
        conn = pika.BlockingConnection(
            pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT)
        )
        ch = conn.channel()
        ch.queue_declare(queue=RABBITMQ_QUEUE_IMAGES, durable=True)
        ch.basic_publish(
            exchange="",
            routing_key=RABBITMQ_QUEUE_IMAGES,
            body=message,
            properties=pika.BasicProperties(delivery_mode=2),
        )
        ch.confirm_delivery()
        conn.close()
        return True
    except AMQPError as e:
        print(f"    -[API] Error RabbitMQ: {e}")
        return False
    except Exception as e:
        print(f"    -[API] Error RabbitMQ: {e}")
        return False


def receive_image_from_IA(photo: PhotoSave) -> None:
    """Recibe una imagen procesada desde la IA y la guarda en disco.

    La imagen viene como string (codificación 1:1, por ejemplo `latin1`),
    compatible con `PhotoSend` del microservicio de IA.
    """
    image_filename = f"{photo.id}.jpg"
    create_directories()
    imgs_dir = os.path.join(os.getcwd(), "services", "imgs")
    os.makedirs(imgs_dir, exist_ok=True)

    # Convertimos el string recibido a bytes antes de escribirlo en disco.
    # Usa la misma codificación que el flujo IA -> API (por defecto latin1).
    raw_bytes = photo.image.encode("latin1")
    with open(os.path.join(imgs_dir, image_filename), "wb") as f:
        f.write(raw_bytes)


def move_images() -> None:
    """Integración del antiguo `move_images.py` para unificar carpetas.

    Mueve imágenes desde:
      - services/pre_pro
      - services/post_pro
      - app/services/imgs  (si existía así)
    hacia:
      - services/imgs
    """
    import shutil

    base = os.getcwd()
    pre_pro_dir = os.path.join(base, "services", "pre_pro")
    post_pro_dir = os.path.join(base, "services", "post_pro")
    imgs_dir_old = os.path.join(base, "app", "services", "imgs")  # si existía así
    final_dir = os.path.join(base, "services", "imgs")
    os.makedirs(final_dir, exist_ok=True)

    for directory in (pre_pro_dir, post_pro_dir, imgs_dir_old):
        if not os.path.exists(directory):
            continue
        for filename in os.listdir(directory):
            src = os.path.join(directory, filename)
            dst = os.path.join(final_dir, filename)
            if not os.path.exists(dst):
                shutil.move(src, final_dir)
