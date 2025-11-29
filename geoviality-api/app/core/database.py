"""Cliente MongoDB y handle global 'db' para la API."""

# stdlib
import os

# third-party
from pymongo.mongo_client import MongoClient
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv("MONGODB_URI")
database = os.getenv("DATABASE_NAME", "geoviality")

client = MongoClient(uri)
try:
    client.admin.command("ping")
    print("You successfully connected to GeoViality database")
except Exception as exc:  # pylint: disable=broad-exception-caught
    # Se mantiene el catch amplio por robustez en arranque
    print(exc)

db = client[database]
