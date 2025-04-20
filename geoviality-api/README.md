## API

Se debe tener Python instalado.

Abrir una terminal en la carpeta `app`.

Ejecutar comando:

```bash
pip install -r requirements.txt
```

Esto instalará los paquetes necesarios.

Luego, ejecutar el comando:

```bash
python main.py
```

Esto levantará el servidor de la API en `http://localhost:$PORT_NUMBER$`.
Con el tunel en la ubicación `http://shark-quick-loon.ngrok-free.app`

## RUTAS

- **POST** /ulpoad/image: sirve para enviar fotos desde la app móvil

    Espera un form con:

        image: File 
        longitude: float
        latitude: float
        date: datetime

- **GET** /download/images_to_process: es la solicitud que usa la IA para obtener un zip con las imágenes a procesar y sus datos asociados

    Retorna lo siguiente:

        zip_file: Any
        metadata: Dict[photo_id ,PhotoCreate]

    PhotoCreate:

        image: str 
        longitude: float
        latitude: float
        date: datetime

- GET /data/processed_info: sirve para obtener todos los puntos guardados en la base de datos

    Retorna una lista con los puntos con el siguiente formato:

            image_filename: str,
            latitude: float,
            longitude: float,
            date: date,
            type: list

- GET /download/get_image/{image_id}: sirve para obtener la imagen {image_id} desde el almacenamiento de la API