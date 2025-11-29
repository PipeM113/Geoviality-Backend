# ia_service/services/files_service.py
import os
from ia_service.core.config import settings
import logging

logger = logging.getLogger(__name__)


def get_base_dir() -> str:
    return settings.IMAGES_BASE_DIR


def get_pre_dir() -> str:
    return settings.IMAGES_PRE_DIR


def get_post_dir() -> str:
    return settings.IMAGES_POST_DIR


def get_pre_image_path(filename: str) -> str:
    return os.path.join(get_pre_dir(), filename)


def get_post_image_path(filename: str) -> str:
    return os.path.join(get_post_dir(), filename)


def get_dataset_path() -> str:
    return os.path.join(get_base_dir(), settings.DATASET_FILENAME)


def create_directories() -> None:
    """
    Crea las carpetas 'imgs', 'imgs/pre' y 'imgs/post' si no existen
    y el archivo 'dataset.csv' (truncándolo como en la versión original).
    """
    base_dir = get_base_dir()
    pre_dir = get_pre_dir()
    post_dir = get_post_dir()

    if not os.path.exists(base_dir):
        os.makedirs(base_dir)

    if not os.path.exists(pre_dir):
        os.makedirs(pre_dir)

    if not os.path.exists(post_dir):
        os.makedirs(post_dir)

    csv_filepath = get_dataset_path()
    # Igual que antes: abrir en 'w' para crear o truncar
    with open(csv_filepath, "w", encoding="utf-8") as csv_file:
        csv_file.write("")
    logger.info("    - [IA] Directorios y dataset.csv preparados.")


def delete_image(image_filename: str) -> None:
    """
    Elimina la imagen 'image_filename' desde la carpeta 'imgs/post',
    equivalente a funcs.delete_image.
    """
    image_path = get_post_image_path(image_filename)
    if os.path.exists(image_path):
        os.remove(image_path)
        logger.info(
            "    - [IA] Imagen '%s' eliminada de 'post_pro'.", image_filename
        )
    else:
        logger.info(
            "    - [IA] Imagen '%s' no encontrada en 'post_pro'.", image_filename
        )
