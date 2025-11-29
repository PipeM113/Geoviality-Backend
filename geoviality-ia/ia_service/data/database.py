# ia_service/data/database.py
from pymongo.mongo_client import MongoClient
from pymongo.errors import PyMongoError
from ia_service.core.config import settings
import logging

logger = logging.getLogger(__name__)

client = MongoClient(settings.MONGODB_URI)

try:
    client.admin.command("ping")
    logger.info("You successfully connected to GeoViality database")
except PyMongoError as e:
    logger.error("Error connecting to MongoDB: %s", e)

db = client[settings.DATABASE_NAME]
