from mongoengine import connect, disconnect
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME", "geoviality")


def init_db() -> None:
    if not MONGO_URI:
        raise RuntimeError("La variable de entorno MONGODB_URI no está definida.")
    connect(
        alias="default",
        host=MONGO_URI,
        db=DATABASE_NAME,
        serverSelectionTimeoutMS=5_000,
        uuidRepresentation="standard",
    )

def close_db() -> None:
    disconnect(alias="default")