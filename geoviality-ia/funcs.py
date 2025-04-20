import requests
from dotenv import load_dotenv
from database import db
import os
from models import PhotoInfo, PhotoDB, PhotoSend, GeoJson, Geometry
from datetime import datetime
import time
import uuid

load_dotenv()

host = os.getenv('HOST', '127.0.0.1')
port = os.getenv('PORT', 8080)

url = f'http://{host}:{port}'

def save_data_to_mongodb(photo_info: PhotoInfo):
    """
    Guarda los datos de la imagen 'image_filename' como 'latitude',
    'longitude', 'date' y 'type' en la BD 'processed_images'
    
    """
    collection = db['processed_geojson']
    
    data = PhotoDB(**photo_info.model_dump(), repair_at=None, estado=0, observaciones="Sin Observaciones")
    irregularidad = geoJson(data)
    
    try:
        result = collection.insert_one(irregularidad)
    except Exception as e:
        print(f"    - [IA] Datos duplicados de la imagen '{photo_info.id}' en la BD, error:", e)

    geojson = GeoJson(**irregularidad)
    
    procesar_irregularidad(geojson)
    
    print(f"    - [IA] Imagen '{photo_info.id}' guardada en 'processed_geojson' con el ID: {result.inserted_id}.")

def actualizar_foto(foto: GeoJson, id_imagen: str):
    """
    Actualiza la foto en la BD 'processed_images' agregando el id de la imagen a la lista de imagenes.
    """
    
    try:
        db.processed_geojson.update_one(
            {"_id": foto.properties.id},
            {
                "$addToSet": {"properties.images": id_imagen},
                "$set": {"properties.last_update": datetime.now()}
            }
        )
        print(f"    - [IA] Foto '{foto.properties.id}' actualizada con la imagen '{id_imagen}'.")
    except Exception as e:
        print(f"    - [IA] Error al actualizar la foto '{foto.properties.id}': {e}")

def procesar(info: PhotoInfo):
    irregularidad = irregularidad_cercana(Geometry(coordinates=[info.longitude, info.latitude]))
    if irregularidad:
        print(f"    - [IA] Irregularidad cercana a la imagen '{info.id}' encontrada.")
        actualizar_foto(irregularidad, info.id)
    else:
        print(f"    - [IA] No se encontró una irregularidad cercana a la imagen '{info.id}'.")
        save_data_to_mongodb(info)

def irregularidad_cercana(punto: Geometry, max_distance=10) -> GeoJson | None :
    """
    Encuentra la irregularidad más cercana a un punto dado usando una consulta geoespacial.
    """
    try:
        punto = db.processed_geojson.find_one({
            "geometry": {
                "$near": {
                    "$geometry": punto.model_dump(),
                    "$maxDistance": max_distance
                }
            }
        })
        return GeoJson(**punto)
    
    except Exception as e:
        print(f"    - [IA] Error al buscar irregularidad cercana: {e}")
        return None

def delete_image(image_filename: str):
    """
    Llama a la API para eliminar la imagen 'image_filename' de 'post_pro' en su disco duro.
    
    Luego, elimina la imagen 'image_filename' de la carpeta 'imgs/post'.
    """
    image_directory = 'imgs/post'
    image_path = os.path.join(image_directory, image_filename)
    if os.path.exists(image_path):
        os.remove(image_path)
        print(f"    - [IA] Imagen '{image_filename}' eliminada de 'post_pro'.")
    else:
        print(f"    - [IA] Imagen '{image_filename}' no encontrada en 'post_pro'.")

def create_directories():
    """
    Crea las carpetas 'imgs', 'imgs/pre' y 'imgs/post' en el directorio actual si no existen
    
    Tambien crea el archivo 'dataset.csv' en la carpeta 'imgs' si no existe
    """
    base_dir = os.path.join(os.getcwd(), "imgs")
    pre_pro_dir = os.path.join(base_dir, "pre")
    post_pro_dir = os.path.join(base_dir, "post")
    
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
    
    if not os.path.exists(pre_pro_dir):
        os.makedirs(pre_pro_dir)
    
    if not os.path.exists(post_pro_dir):
        os.makedirs(post_pro_dir)

    csv_filename = 'dataset.csv'
    csv_filepath = os.path.join(base_dir, csv_filename)
    with open(csv_filepath, 'w') as csv_file:
        pass

def send_to_API(data: PhotoSend):
    """
    Envia los datos de la imagen 'image' y 'image_filename' a la api
    """
    retries = 0
    max_retries = 3
    while retries < max_retries:
        try:
            request_url = f'{url}/data/processed_image'
            response = requests.post(request_url, json=data.model_dump())
            response.raise_for_status()
            print(f"    - [IA] Imagen '{data.id}' enviada a la API.")
            break
        except requests.exceptions.RequestException as e:
            print(f"    - [IA] Error al enviar la imagen '{data.id}' a la API: {e}")
            print(f"    - [IA] Reintentando en 5 segundos...")
            time.sleep(5)
            retries += 1
    if retries == max_retries:
        print(f"    - [IA] No se pudo enviar la imagen '{data.id}' a la API.")

def geoJson(data: PhotoDB) -> dict:
    properties = {}
    item = data.model_dump()
    item["_id"] = str(uuid.uuid4())
    item["images"] = [item["id"]]
    item["id"] = item["_id"]
    for key in item:
        if key!="longitude" and key!="latitude" and key!="_id":
            properties[key] = item[key]
    properties["last_update"] = datetime.now()
    geojson = {
        "_id": item["_id"],
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [item["longitude"], item["latitude"]]
        },
        "properties": properties 
    }
    return geojson

def encontrar_calle_mas_cercana(punto : Geometry , max_distance = 30) -> dict:
    """
    Encuentra la calle más cercana a un punto dado usando una consulta geoespacial.
    """
    return db.streets.find_one({
        "geometry": {
            "$near": {
                "$geometry": punto.model_dump(),
                "$maxDistance": max_distance
            }
        }
    })

def actualizar_calle_con_irregularidades(calle_id: str, id_imagen: str ,tipos_irregularidades : list[str]):
    """
    Actualiza la calle incrementando cada tipo de irregularidad proporcionado.
    """
    incrementos = {f"properties.{tipo}": 1 for tipo in tipos_irregularidades}

    db.streets.update_one(
        {"id": calle_id},
        {
            "$inc": incrementos,
            "$addToSet": {"properties.images": id_imagen},
            "$set": {"properties.last_update": datetime.now()}
        }
    )

def procesar_irregularidad(irregularidad: GeoJson):
    """
    Procesa una nueva irregularidad: encuentra la calle más cercana y actualiza sus propiedades.
    """
    punto = irregularidad.geometry
    tipos_irregularidades = [tipo.capitalize() for tipo in irregularidad.properties.type]

    calle = encontrar_calle_mas_cercana(punto)

    if calle:
        calle_id = calle["id"]
        actualizar_calle_con_irregularidades(calle_id,irregularidad.properties.id ,tipos_irregularidades)
        print(f"    - [IA] Irregularidad procesada en la calle '{calle_id}'.")
    else:
        print(f"    - [IA] No se encontró una calle cercana a la irregularidad.")

""" Cementerio:

def procesar_dato_hist(punto: GeoJson):
    #Procesa un punto y actualiza la coleccion de datos históricos.
    fecha = punto.properties.date.isoformat()
    tipos = punto.properties.type

    anio = int(fecha[:4])
    mes = fecha[5:7]  
    nombre_mes = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio","Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"][int(mes) - 1]
    incrementos = {f"irregularidadesPorTipo.{tipo}": 1 for tipo in tipos}
    incrementos["irregularidadesTotales"] = len(tipos)

    db.historical_data.update_one(
        {"anio": anio, "mes": nombre_mes},
        {
            "$inc": incrementos
        }
    )

def move_image(image_filename : str):

    #Llamada a la API para mover la imagen 'image_filename' desde 'pre_pro' a 'post_pro' en su disco duro

    api_url = f'{url}/data/processed_image/{image_filename}'
    response = requests.put(api_url)
    response.raise_for_status()
    print(f"    - [API] Imagen '{image_filename}' movida exitosamente de 'pre_pro' a 'post_pro'.")


def get_images():
    
    #Llama a la API para obtener los datos de la BD 'images_to_process' y las descarga desde la API en la carpeta 'imgs/pre'
    
    data= list(db.images_to_process.find())
    for i in data:
        print(f"    - Descargando imagen '{i['image_filename']}' en 'imgs/pre'...")
        response = requests.get(f'{url}/download/get_pre_image/{i["image_filename"]}')
        response.raise_for_status()
        with open(f'imgs/pre/{i["image_filename"]}', 'wb') as image_file:
            image_file.write(response.content)

def send_images():
    api_url = f'{url}/upload/processed_images'

    image_directory = 'imgs/post'

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for filename in os.listdir(image_directory):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                file_path = os.path.join(image_directory, filename)
                zip_file.write(file_path, arcname=filename)

    zip_buffer.seek(0)

    try:
        files = {'file': ('images.zip', zip_buffer, 'application/zip')}
        response = requests.post(api_url, files=files)
        response.raise_for_status()
        print("Archivo ZIP enviado exitosamente.")
    except requests.exceptions.RequestException as e:
        print(f"Error al enviar el archivo ZIP: {e}")

def get_image_data(image_filename):

    #Obtiene los datos de la imagen 'image_filename' desde la BD 'images_to_process'
    
    #Esto incluye campos como 'image_filename', 'latitude', 'longitude', 'date' y 'modo'

    collection = db['images_to_process']
    query = {"image_filename": image_filename}
    result = collection.find_one(query)
    return result

def remove_from_db_delete(image_filename):

    #Elimina la imagen 'image_filename' de la BD 'images_to_delete'

    collection = db['images_to_delete']
    query = {"image_filename": image_filename}
    result = collection.delete_one(query)
    print(f"- [DB] Imagen '{image_filename}' eliminada de 'images_to_delete'.\n")

def get_images_to_delete_db():
    #Obtiene los datos de la BD 'images_to_delete' y devuelve una lista con los nombres de las imagenes a borrar.

    collection = db['images_to_delete']
    data = list(collection.find())
    return [i['image_filename'] for i in data]

def mark_image_for_deletion_db(image_filename):
    
    #Guarda en la BD 'images_to_delete' la imagen 'image_filename'.

    collection = db['images_to_delete']
    
    data = {
        "_id": str(ObjectId()),
        "image_filename": image_filename
    }
    
    result = collection.insert_one(data)

    print(f"    - [DB] Imagen '{image_filename}' MARCADA en 'images_to_delete' con el ID: {result.inserted_id}.")   

def delete_from_db_pre(image_filename):

    #Elimina la imagen 'image_filename' de la BD 'images_to_process'
    
    collection = db['images_to_process']
    query = {"image_filename": image_filename}
    result = collection.delete_one(query)
    print(f"- [DB] Imagen '{image_filename}' eliminada de 'images_to_process'.")    

"""