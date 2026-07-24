import logging

from fastapi import FastAPI
from app.api.faq_router import router as faq_router
from app.api.chat_router import router as chat_router
from app.api.ingest_router import router as ingest_router
from app.api.auth_router import router as auth_router
from app.core.mongo import ensure_indexes
from fastapi.middleware.cors import CORSMiddleware

# Show INFO-level logs from our app modules (e.g. intent detection). Without
# this, app loggers fall through to the root logger, which defaults to WARNING
# and prints nothing — uvicorn only configures its own loggers.
logging.basicConfig(level=logging.INFO)

app = FastAPI()


@app.on_event("startup")
def on_startup():
    ensure_indexes()


origins = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://localhost:8082",
    "http://127.0.0.1:8082",
    "https://purple-sea-0b1db0900.4.azurestaticapps.net"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(faq_router)
app.include_router(chat_router)
app.include_router(ingest_router)
app.include_router(auth_router)
