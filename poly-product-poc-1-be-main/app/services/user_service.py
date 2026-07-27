from bson import ObjectId

from app.core.mongo import ensure_indexes, user_collection
from app.core.security import hash_password, verify_password


class UserService:

    @staticmethod
    def get_by_email(email: str):
        return user_collection.find_one({"email": email})

    @staticmethod
    def get_by_id(user_id: str):
        try:
            oid = ObjectId(user_id)
        except Exception:
            return None
        return user_collection.find_one({"_id": oid})

    @staticmethod
    def create_user(email: str, password: str) -> str:
        # Make sure the unique-email index exists before the first insert, so
        # duplicate registrations are rejected by the database too.
        ensure_indexes()
        if UserService.get_by_email(email):
            raise ValueError("Email already registered")

        doc = {
            "email": email,
            "password_hash": hash_password(password),
        }
        user_id = user_collection.insert_one(doc).inserted_id
        return str(user_id)

    @staticmethod
    def authenticate(email: str, password: str):
        user = UserService.get_by_email(email)
        if not user or not verify_password(password, user["password_hash"]):
            return None
        return user
