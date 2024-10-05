import os
from pymongo import MongoClient

mongo_url = os.getenv("MONGO_URI")

if mongo_url is None:
    raise ValueError("MONGO_URI environment variable not set")

client = MongoClient(mongo_url)

db = client.get_database()
