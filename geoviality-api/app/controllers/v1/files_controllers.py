from pathlib import Path
import pika
from pika.exceptions import AMQPError
from fastapi import HTTPException, status

from schemas.v1.files_schemas import PhotoQueue, PhotoSave

def send_to_queue(data: PhotoQueue) -> None:
    connection = None
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq"))
        channel = connection.channel()
        channel.queue_declare(queue="images", durable=True)
        channel.basic_publish(
            exchange="",
            routing_key="images",
            body=data.model_dump_json(),
            properties=pika.BasicProperties(delivery_mode=2),
        )
        channel.confirm_delivery()
    except AMQPError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se pudo conectar con RabbitMQ."
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error inesperado al enviar la imagen a la cola."
        ) from exc
    finally:
        if connection and not connection.is_closed:
            connection.close()

def receive_image_from_IA(photo: PhotoSave) -> None:
    image_bytes = photo.image.encode("latin1")
    image_dir = Path("services") / "imgs"
    image_dir.mkdir(parents=True, exist_ok=True)
    image_path = image_dir / f"{photo.id}.jpg"
    try:
        with image_path.open("wb") as image_file:
            image_file.write(image_bytes)
    except OSError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo guardar la imagen procesada en disco."
        ) from exc
    print(f"    -[API] Imagen '{photo.id}' recibida y guardada en 'imgs'.")