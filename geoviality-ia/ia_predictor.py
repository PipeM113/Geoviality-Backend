from ultralytics import YOLO
import torch
import cv2
import os
import csv
from funcs import save_data_to_mongodb, procesar
from models import PhotoDB
from bson.objectid import ObjectId
from models import PhotoInfo

def ia_imagenes(car_model, walk_model, input_source, output_directory, dataset_directory, confianza, diccionario):
    """
    car_model: Modelo de IA para vehiculos.
    walk_model: Modelo de IA para peatones.
    input_source: Ruta de la imagen a procesar
    output_directory: Ruta de la imagen procesada
    dataset_directory: Ruta del archivo CSV
    confianza: Umbral de confianza para las detecciones

    Retorna True si la imagen NO tiene detecciones, False en caso contrario.
    
    Si hay detecciones, esta funcion manda a guardar los datos en la BD 'processed_images' junto con las detecciones.
    
    Tanto si hay detecciones como si no, se manda a la API a mover la imagen a la carpeta 'post_pro'.
    """
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # print("\nia_predictor/ia_imagenes - Diccionario", diccionario, "\n")

    if diccionario['modo'] == 'auto':
        print("    - Modelo de IA: Vehiculo")
        model = YOLO(car_model)
    else:
        print("    - Modelo de IA: Peaton")
        model = YOLO(walk_model)

    try:
        class_names = model.names
    except AttributeError:
        class_names = ['hoyo', 'hoyo con agua', 'cocodrilo', 'cocodrilo con agua', 'lomo de toro', 'grieta', 'longitudinal']

    input_extension = os.path.splitext(input_source)[1].lower()
    #is_video = input_extension in ['.mp4', '.avi', '.mov', '.mkv', '.TS', '.ts']
    is_image = input_extension in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.TS', '.ts']

    log_data = []

    if is_image:
        frame = cv2.imread(input_source)
        try:
            frame = cv2.imread(input_source)
            if frame is None:
                raise FileNotFoundError(f"Error al abrir la imagen: {input_source}")
        except Exception as e:
            print(f"Excepción encontrada: {e}")
            return # !!!PELIGROSO!!! (No se retorna nada)

        results = model.predict(frame, conf=confianza, device=device) # Esto imprime la detección en consola

        for result in results:
            annotated_frame = result.plot()
            cv2.imwrite(output_directory, annotated_frame) # Guardar la imagen procesada en el directorio de salida

            for detection in result.boxes:
                class_index = int(detection.cls.item())
                class_name = class_names[class_index] if class_index < len(class_names) else 'Unknown'

                log_entry = {
                    'class': class_name,
                    'confidence': round(detection.conf.item() * 100, 2)
                }
                log_data.append(log_entry)

    else:
        print("Tipo de archivo no compatible.")
        exit() # !!!PELIGROSO!!! (Crash)

    csv_filename = 'dataset.csv'
    csv_filepath = os.path.join(dataset_directory, csv_filename)

    with open(csv_filepath, mode='a', newline='') as csv_file:
        fieldnames = ['id', 'class', 'confidence']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

        if csv_file.tell() == 0:
            writer.writeheader()

        diccionario['type'] = [] # 'class' es una lista de las clases detectadas en la imagen.
        for log_entry in log_data:
            if log_entry['confidence'] >= confianza:
                log_entry['id'] = diccionario['id']
                writer.writerow(log_entry)
                if log_entry['class'] not in diccionario['type']:
                    diccionario['type'].append(log_entry['class'])
        if diccionario['type'] == []:
            return True
        else:
            procesar(PhotoInfo(**diccionario))
            print(f" [IA]: imagen {diccionario['id']} guardada en BDD")
            return False


"""Cementerio

    if is_video:
        # Leer el video original
        cap = cv2.VideoCapture(input_source)
        if not cap.isOpened():
            print("Error al abrir el video.")
            exit()

        # Obtener las propiedades del video
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))

        # Configurar el escritor de video para guardar el video procesado
        output_path = output_directory
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Codec para el archivo de salida
        out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))

        # Realizar la predicción y guardar cada fotograma procesado en el video de salida
        frame_number = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Realizar la predicción en el fotograma actual
            results = model.predict(frame, conf=confianza, device=device)

            # Dibujar las predicciones en el fotograma
            for result in results:
                annotated_frame = result.plot()
                out.write(annotated_frame)  # Guardar el fotograma procesado en el video de salida

                # Extraer información de las detecciones
                for detection in result.boxes:
                    class_index = int(detection.cls.item())
                    class_name = class_names[class_index] if class_index < len(class_names) else 'Unknown'

                    log_entry = {
                        'frame_number': frame_number,
                        'timestamp': f"{frame_number // fps} [seg]",
                        'class': class_name,
                        'confidence': f"{round(detection.conf.item() * 100, 2)}%",
                        'x_min': detection.xyxy[0][0].item(),
                        'y_min': detection.xyxy[0][1].item(),
                        'x_max': detection.xyxy[0][2].item(),
                        'y_max': detection.xyxy[0][3].item()
                    }
                    log_data.append(log_entry)

            frame_number += 1

        # Liberar recursos del video
        cap.release()
        out.release()
"""