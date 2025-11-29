# ia_service/processing/predictor.py

from ultralytics import YOLO
import torch
import cv2
import os
import csv
from typing import Dict, Any, List
from ia_service.core.config import settings
import logging

logger = logging.getLogger(__name__)


def ia_imagenes(
    car_model: str,
    walk_model: str,
    input_source: str,
    output_directory: str,
    dataset_directory: str,
    confianza: float,
    diccionario: Dict[str, Any],
) -> bool:
    """
    Ejecuta la detección con YOLO sobre una imagen, guarda la imagen anotada,
    registra detecciones en dataset.csv y rellena diccionario["type"].

    Parámetros:
        car_model: Ruta del modelo de IA para vista vehículo.
        walk_model: Ruta del modelo de IA para vista peatón.
        input_source: Ruta de la imagen a procesar (en imgs/pre).
        output_directory: Ruta de salida de la imagen procesada (en imgs/post).
        dataset_directory: Directorio donde vive dataset.csv.
        confianza: Umbral de confianza de detección (0-1).
        diccionario: Diccionario con metadatos de la imagen; se modificará
                     agregando/actualizando la clave "type" (lista de strings).

    Retorna:
        True  -> NO hay detecciones.
        False -> SÍ hay detecciones.

    Efectos secundarios:
        - Escribe/actualiza dataset.csv con columnas: id, class, confidence.
        - Guarda la imagen anotada en output_directory.
        - Actualiza diccionario["type"] con los nombres de clases detectadas.
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    modo = diccionario.get("modo", "auto")
    if modo == "auto":
        logger.info("    - Modelo de IA: Vehiculo")
        model = YOLO(car_model)
    else:
        logger.info("    - Modelo de IA: Peaton")
        model = YOLO(walk_model)

    # USAR model.names DIRECTAMENTE (puede ser dict o lista)
    try:
        class_names = model.names  # normalmente dict {0: 'clase0', 1: 'clase1', ...}
    except AttributeError:
        # Fallback por si el modelo no tiene names definidos
        class_names = [
            "hoyo",
            "hoyo con agua",
            "cocodrilo",
            "cocodrilo con agua",
            "lomo de toro",
            "grieta",
            "longitudinal",
        ]

    input_extension = os.path.splitext(input_source)[1].lower()
    is_image = input_extension in [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".ts"]

    log_data: List[Dict[str, Any]] = []

    if is_image:
        try:
            frame = cv2.imread(input_source)
            if frame is None:
                raise FileNotFoundError(f"Error al abrir la imagen: {input_source}")
        except Exception as e:  # noqa: BLE001
            logger.error("Excepción encontrada al leer imagen: %s", e)
            # Por seguridad, tratamos como "sin detecciones"
            return True

        results = model.predict(frame, conf=confianza, device=device)

        for result in results:
            annotated_frame = result.plot()
            cv2.imwrite(output_directory, annotated_frame)

            for detection in result.boxes:
                class_index = int(detection.cls.item())

                # Sacar SIEMPRE un string de class_names
                if isinstance(class_names, dict):
                    class_name = class_names.get(class_index, str(class_index))
                elif isinstance(class_names, (list, tuple)):
                    class_name = (
                        class_names[class_index]
                        if 0 <= class_index < len(class_names)
                        else str(class_index)
                    )
                else:
                    class_name = str(class_index)

                log_entry = {
                    "class": str(class_name),  # aseguramos string
                    # mantenemos escala 0-100 como en tu código original
                    "confidence": round(detection.conf.item() * 100, 2),
                }
                log_data.append(log_entry)
    else:
        logger.error("Tipo de archivo no compatible: %s", input_extension)
        return True

    # Manejo de dataset.csv
    csv_filepath = os.path.join(dataset_directory, settings.DATASET_FILENAME)

    with open(csv_filepath, mode="a", newline="", encoding="utf-8") as csv_file:
        fieldnames = ["id", "class", "confidence"]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

        if csv_file.tell() == 0:
            writer.writeheader()

        diccionario["type"] = []
        for log_entry in log_data:
            # Ojo: en el código original se comparaba confianza 0-100 vs 0.65.
            # Mantenemos la misma semántica (aunque sea rara) para no romper resultados previos.
            if log_entry["confidence"] >= confianza:
                log_entry["id"] = diccionario["id"]
                writer.writerow(log_entry)
                if log_entry["class"] not in diccionario["type"]:
                    diccionario["type"].append(log_entry["class"])

    # True si NO hay detecciones, False si SÍ hay (contrato original)
    if not diccionario["type"]:
        return True
    else:
        return False
