from datetime import datetime

from pydantic import BaseModel


class ConversationOut(BaseModel):
    id: str
    user_id: str
    # First user message, truncated — set once by add_message() and never
    # overwritten. None for a conversation that has no messages yet.
    title: str | None = None
    created_at: datetime
    updated_at: datetime


class MessageOut(BaseModel):
    id: str
    conversation_id: str
    user_id: str
    role: str
    content: str
    # FAQ/context source the answer was grounded in; left empty for now, but
    # every message record carries the field so it can be filled in later
    # without a schema change.
    source: str = ""
    timestamp: datetime
