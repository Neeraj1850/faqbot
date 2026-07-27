import certifi
from pymongo import MongoClient
from app.core.config import settings

# Atlas connections (mongodb+srv://) use TLS, and passing a CA bundle also
# turns TLS on. A plain local MongoDB (mongodb://localhost) speaks no TLS, so
# we must NOT set tlsCAFile there or the handshake fails. Only hand certifi's
# bundle to the driver for the srv/TLS case, where a missing system CA is a
# common cause of SSL: CERTIFICATE_VERIFY_FAILED on macOS.
uri = settings.MONGO_URI
uses_tls = uri.startswith("mongodb+srv://") or "tls=true" in uri.lower()
if uses_tls:
    mongo = MongoClient(uri, tlsCAFile=certifi.where())
else:
    mongo = MongoClient(uri)
db = mongo[settings.DB_NAME]
faq_collection = db["faq"]
user_collection = db["users"]


# Whether the unique-email index has already been created this process, so we
# only pay for it once instead of on every registration.
_indexes_ready = False


def ensure_indexes():
    """Create the indexes the app relies on, lazily.

    Called the first time we touch the users collection rather than at startup,
    so the server can boot even when MongoDB is unreachable — the DB error then
    surfaces on the request that actually needs it, not at launch.
    """
    global _indexes_ready
    if _indexes_ready:
        return
    user_collection.create_index("email", unique=True)
    _indexes_ready = True
