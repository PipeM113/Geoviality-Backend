# ia_service/app.py
import logging

from ia_service.core.logging import setup_logging
from ia_service.services.files_service import create_directories
from ia_service.mq.listener import start_listener


def main() -> None:
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("    - [IA] Iniciando IA...")
    create_directories()
    logger.info("    - [IA] Directorios creados.")
    start_listener()


if __name__ == "__main__":
    main()
