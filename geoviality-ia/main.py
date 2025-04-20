import ia_predictor as ia
import dotenv
import pika
import os
import json
import time
from models import PhotoSend

dotenv.load_dotenv()

from funcs import create_directories, delete_image, send_to_API

modelo_IA_auto = os.getcwd() + '/Modelo 2 (Fuerte en Seco)/Vista_Vehiculo_V3.pt'
modelo_IA_peaton = os.getcwd() + '/Modelo 2 (Fuerte en Seco)/Vista_Peaton_General_V3_Refactorizado_Cris.pt'
confianza = 0.65
path_post = os.getcwd() + '/imgs/post/'
path_csv = os.getcwd() + '/imgs/'


def callback(ch, method, properties, body):
    print("    - [IA] Imagen recibida")
    data = json.loads(body)
    print(data.keys())
    image = data['image']
    image_filename = data['id'] + '.jpg'
    id = data['id']
    path = os.getcwd() + '/imgs/pre/' + image_filename
    with open(path, 'wb') as f:
        f.write(image.encode('latin1'))
    print(f"    - [IA] Imagen '{image_filename}' guardada en 'pre' y empezando a procesar.")
    result = ia.ia_imagenes(modelo_IA_auto, modelo_IA_peaton, path, path_post + image_filename, path_csv, confianza, data)
    if result:
        delete_image(image_filename)
    else:
        send_to_API(PhotoSend(image=image, id=id))
    os.remove(path)
    print(f"    - [IA] Imagen '{image_filename}' procesada y eliminada de 'pre'.")
    ch.basic_ack(delivery_tag=method.delivery_tag)

def procesar_imagenes():
    print("    - [IA] Iniciando IA...")
    create_directories()
    print("    - [IA] Directorios creados.")
    print("    - [IA] Iniciando conexión a cola RabbitMQ...")
    while True:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
            print("    - [IA] Conexion a cola Rabbit exitosa.")
            break
        except pika.exceptions.AMQPConnectionError:
            print("    - [IA] No se pudo conectar a RabbitMQ, reintentando en 5 segundos...")
            time.sleep(5)

    channel = connection.channel()
    channel.queue_declare(queue='images', durable=True)
    print('    - [IA] Esperando mensajes, para salir presione CTRL+C')
    channel.basic_consume(
        queue='images', 
        on_message_callback=callback
        )
    channel.start_consuming()

if __name__ == "__main__":
    procesar_imagenes()