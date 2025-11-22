import os
import uuid
import pika
from pika.exceptions import AMQPError
from fastapi import HTTPException, status

from app.core.config import RABBITMQ_HOST, RABBITMQ_QUEUE_IMAGES, RABBITMQ_PORT
from app.core.utils import create_directories
from app.files.v1.files_schemas import PhotoQueue, PhotoSave

def send_to_queue(data: PhotoQueue) -> bool:
    message = data.model_dump_json()
    try:
        conn = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT))
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
    # Guardado local similar a tu lógica actual
    image_filename = f"{photo.id}.jpg"
    create_directories()
    imgs_dir = os.path.join(os.getcwd(), "services", "imgs")
    os.makedirs(imgs_dir, exist_ok=True)
    with open(os.path.join(imgs_dir, image_filename), "wb") as f:
        f.write(photo.image)

def move_images() -> None:
    """Integración del antiguo move_images.py (sin dejarlo suelto)."""
    import shutil
    base = os.getcwd()
    pre_pro_dir  = os.path.join(base, "services", "pre_pro")
    post_pro_dir = os.path.join(base, "services", "post_pro")
    imgs_dir_old = os.path.join(base, "app", "services", "imgs")  # si existía así
    final_dir    = os.path.join(base, "services", "imgs")
    os.makedirs(final_dir, exist_ok=True)

    for directory in (pre_pro_dir, post_pro_dir, imgs_dir_old):
        if not os.path.exists(directory):
            continue
        for filename in os.listdir(directory):
            src = os.path.join(directory, filename)
            dst = os.path.join(final_dir, filename)
            if not os.path.exists(dst):
                shutil.move(src, final_dir)
