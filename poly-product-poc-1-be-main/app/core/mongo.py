from pymongo import MongoClient
from app.core.config import settings

mongo = MongoClient(settings.MONGO_URI)
db = mongo[settings.DB_NAME]
faq_collection = db["faq"]
user_collection = db["users"]


def ensure_indexes():
    user_collection.create_index("email", unique=True)
