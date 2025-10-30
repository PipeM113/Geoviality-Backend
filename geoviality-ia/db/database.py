from pymongo.mongo_client import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

uri = os.getenv("MONGODB_URI")
database = os.getenv("DATABASE_NAME", "geoviality")
client = MongoClient(uri)
try:
    client.admin.command('ping')
    print("You successfully connected to GeoViality database")
except Exception as e:
    print(e)

db = client[database]