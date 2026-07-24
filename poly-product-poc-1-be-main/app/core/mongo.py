from pymongo import MongoClient
from app.core.config import settings

mongo = MongoClient(settings.MONGO_URI)
db = mongo[settings.DB_NAME]
faq_collection = db["faq"]
