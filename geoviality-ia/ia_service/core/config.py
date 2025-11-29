# ia_service/core/config.py
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    def __init__(self) -> None:
        # --- RabbitMQ ---
        self.RABBITMQ_HOST: str = os.getenv("RABBITMQ_HOST", "localhost")
        self.RABBITMQ_PORT: int = int(os.getenv("RABBITMQ_PORT", "5601"))
        self.RABBITMQ_USER: str | None = os.getenv("RABBITMQ_USER")
        self.RABBITMQ_PASSWORD: str | None = os.getenv("RABBITMQ_PASSWORD")

        # --- MongoDB ---
        self.MONGODB_URI: str = os.getenv(
            "MONGODB_URI", "mongodb://localhost:27017"
        )
        self.DATABASE_NAME: str = os.getenv("DATABASE_NAME", "geoviality")

        # --- API externa (backend principal) ---
        self.API_HOST: str = os.getenv("HOST", "127.0.0.1")
        self.API_PORT: int = int(os.getenv("PORT", "8080"))
        self.API_BASE_URL: str = f"http://{self.API_HOST}:{self.API_PORT}"

        # --- Modelos de IA ---
        cwd = os.getcwd()
        default_model_dir = os.path.join(cwd, "Modelo 2 (Fuerte en Seco)")

        self.CAR_MODEL_PATH: str = os.getenv(
            "CAR_MODEL_PATH",
            os.path.join(default_model_dir, "Vista_Vehiculo_V3.pt"),
        )
        self.WALK_MODEL_PATH: str = os.getenv(
            "WALK_MODEL_PATH",
            os.path.join(
                default_model_dir,
                "Vista_Peaton_General_V3_Refactorizado_Cris.pt",
            ),
        )

        # Confianza (umbral) de detección (igual que antes: 0.65)
        self.DETECTION_CONFIDENCE: float = float(
            os.getenv("DETECTION_CONFIDENCE", "0.65")
        )

        # --- Directorios de imágenes / dataset ---
        self.IMAGES_BASE_DIR: str = os.getenv(
            "IMAGES_BASE_DIR", os.path.join(cwd, "imgs")
        )
        self.IMAGES_PRE_DIR: str = os.path.join(self.IMAGES_BASE_DIR, "pre")
        self.IMAGES_POST_DIR: str = os.path.join(self.IMAGES_BASE_DIR, "post")
        self.DATASET_FILENAME: str = "dataset.csv"

        # --- Feature flag para futuro MS de puntos ---
        self.USE_POINTS_MS: bool = (
            os.getenv("USE_POINTS_MS", "false").lower() == "true"
        )
        self.POINTS_QUEUE: str = os.getenv("POINTS_QUEUE", "points")


settings = Settings()
