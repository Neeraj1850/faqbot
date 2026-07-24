"""Conversation + message persistence.

Two flat collections rather than an embedded messages array on the
conversation document: each message is its own record (conversation_id,
user_id, content, role, timestamp, source), which is both what's required
and what scales an append-heavy chat history — no growing-array document,
a plain indexed collection instead.

Ownership is checked on every read/write that takes a conversation_id: a
conversation belonging to another user is treated as not found (ValueError),
never silently exposed. The router translates ValueError into HTTP 404, the
same convention already used for "email already registered" in
UserService/auth_router.
"""

from datetime import datetime, timezone

from bson import ObjectId

from app.core.mongo import conversation_collection, message_collection


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _conversation_out(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "user_id": doc["user_id"],
        "created_at": doc["created_at"],
        "updated_at": doc["updated_at"],
    }


def _message_out(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "conversation_id": doc["conversation_id"],
        "user_id": doc["user_id"],
        "role": doc["role"],
        "content": doc["content"],
        "source": doc.get("source", ""),
        "timestamp": doc["timestamp"],
    }


class ConversationService:
    @staticmethod
    def create_conversation(user_id: str) -> dict:
        """Start a new conversation for ``user_id``. Returns the conversation."""
        now = _now()
        doc = {"user_id": user_id, "created_at": now, "updated_at": now}
        doc["_id"] = conversation_collection.insert_one(doc).inserted_id
        return _conversation_out(doc)

    @staticmethod
    def get_conversation(conversation_id: str, user_id: str) -> dict | None:
        """Fetch a conversation iff it exists and belongs to ``user_id``.

        A conversation belonging to another user reads as missing, the same
        isolation pattern ``LearningManager.get_learning`` uses in the
        learnings service: callers can safely 404 on ``None``.
        """
        try:
            oid = ObjectId(conversation_id)
        except Exception:
            return None
        doc = conversation_collection.find_one({"_id": oid, "user_id": user_id})
        return _conversation_out(doc) if doc else None

    @staticmethod
    def add_message(
        conversation_id: str,
        user_id: str,
        role: str,
        content: str,
        source: str = "",
    ) -> dict:
        """Append a message to an existing, owned conversation.

        Raises ``ValueError`` if the conversation doesn't exist or belongs
        to a different user — callers convert this to a 404.
        """
        if ConversationService.get_conversation(conversation_id, user_id) is None:
            raise ValueError(f"conversation not found: {conversation_id}")

        now = _now()
        doc = {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "role": role,
            "content": content,
            "source": source,
            "timestamp": now,
        }
        doc["_id"] = message_collection.insert_one(doc).inserted_id

        # Bump the parent so "list conversations, most recent first" reflects
        # actual activity, not just when the conversation was first created.
        conversation_collection.update_one(
            {"_id": ObjectId(conversation_id)}, {"$set": {"updated_at": now}}
        )
        return _message_out(doc)

    @staticmethod
    def get_messages(conversation_id: str, user_id: str) -> list[dict]:
        """Full message history for one conversation, oldest first.

        Raises ``ValueError`` if the conversation doesn't exist or isn't
        owned by ``user_id`` (see ``add_message``).
        """
        if ConversationService.get_conversation(conversation_id, user_id) is None:
            raise ValueError(f"conversation not found: {conversation_id}")

        cursor = message_collection.find({"conversation_id": conversation_id}).sort(
            "timestamp", 1
        )
        return [_message_out(doc) for doc in cursor]

    @staticmethod
    def list_conversations(user_id: str, limit: int = 50) -> list[dict]:
        """This user's conversations, most recently active first."""
        cursor = (
            conversation_collection.find({"user_id": user_id})
            .sort("updated_at", -1)
            .limit(limit)
        )
        return [_conversation_out(doc) for doc in cursor]
