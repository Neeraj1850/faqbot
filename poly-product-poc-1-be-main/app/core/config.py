import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    DB_NAME = os.getenv("DB_NAME", "faq_db")
    PINECONE_INDEX = os.getenv("PINECONE_INDEX", "faqbot")
    PINECONE_NAMESPACE = ""
    # Google Gemini embeddings (free tier). gemini-embedding-001 is configured
    # to output 1536-dim vectors to match the existing Pinecone index.
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")
    EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))

    # JWT — signs the tokens handed out by /auth/login and /auth/register.
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

    # polynomial-learnings (two-tier HTTP integration). All optional: when
    # LEARNINGS_BASE_URL is empty the learning module is fully disabled and both
    # retrieval and persistence become no-ops, so the bot behaves exactly as before.
    LEARNINGS_BASE_URL = os.getenv("LEARNINGS_BASE_URL", "")
    LEARNINGS_AGENT_ID = os.getenv("LEARNINGS_AGENT_ID", "faqbot")
    LEARNINGS_RETRIEVE_LIMIT = int(os.getenv("LEARNINGS_RETRIEVE_LIMIT", "5"))
    LEARNINGS_TIMEOUT = float(os.getenv("LEARNINGS_TIMEOUT", "5.0"))
    LEARNINGS_MIN_QUERY_LEN = int(os.getenv("LEARNINGS_MIN_QUERY_LEN", "3"))
    # How many learnings to load per scope when listing them for a chat turn.
    LEARNINGS_LIST_LIMIT = int(os.getenv("LEARNINGS_LIST_LIMIT", "50"))

    # Groq — powers the "detect intent" step that decides whether a conversation
    # is worth persisting as a learning. When GROQ_API_KEY is unset, intent
    # detection is skipped and /chat/persist becomes a no-op.
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

settings = Settings()
