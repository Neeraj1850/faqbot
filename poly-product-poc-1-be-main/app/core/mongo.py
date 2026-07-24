from pymongo import MongoClient
from app.core.config import settings

mongo = MongoClient(settings.MONGO_URI)
db = mongo[settings.DB_NAME]
faq_collection = db["faq"]
user_collection = db["users"]
conversation_collection = db["conversations"]
message_collection = db["messages"]


def ensure_indexes():
    user_collection.create_index("email", unique=True)
    # Powers "list this user's conversations, most recently updated first".
    # 1 = ascending, -1 = descending (what pymongo.ASCENDING/DESCENDING alias
    # to) — used as literals so this module doesn't need those names, which
    # the test suite's lightweight pymongo stub (see tests/conftest.py) does
    # not define.
    conversation_collection.create_index([("user_id", 1), ("updated_at", -1)])
    # Powers "fetch this conversation's messages in order".
    message_collection.create_index([("conversation_id", 1), ("timestamp", 1)])
