from datetime import datetime

from pydantic import BaseModel


class ConversationOut(BaseModel):
    id: str
    user_id: str
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
