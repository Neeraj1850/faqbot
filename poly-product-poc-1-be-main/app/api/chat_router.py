import logging

from fastapi import APIRouter, Depends, HTTPException, status
from app.services.llm_service import LLMService
from app.services import (
    learnings_api,
    intent_service,
    faq_search_service,
)
from app.services.conversation_service import ConversationService
from app.models.conversation_model import ConversationOut, MessageOut
from pydantic import BaseModel
from app.dependencies.auth import get_current_user

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/chat")

# Shown when the message is abusive or outside what this bot covers.
REFUSAL_MESSAGE = (
    "I'm sorry, but I can't help with that. I can answer questions about our "
    "products and services — feel free to ask me one of those."
)


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    query: str
    # Optional earlier turns from the chatbox, giving the learning judge context.
    messages: list[Message] | None = None
    # Omit to start a new chat (the default when opening the app); pass an
    # id from GET /chat/conversations to continue an older one.
    conversation_id: str | None = None


def _resolve_conversation_id(requested_id: str | None, entity_id: str) -> str | None:
    """Reuse ``requested_id`` if it's a real conversation owned by this user,
    otherwise start a new one. Fail-open like every other dependency in this
    router: if Mongo is unreachable, conversation persistence is skipped for
    this turn (``None``) rather than failing the whole chat request.
    """
    if requested_id:
        try:
            existing = ConversationService.get_conversation(requested_id, entity_id)
            if existing is not None:
                return existing["id"]
            logger.warning(
                "conversation_id %r not found for this user; starting a new one",
                requested_id,
            )
        except Exception as exc:
            logger.warning(
                "failed to look up conversation_id %r: %s", requested_id, exc
            )

    try:
        return ConversationService.create_conversation(entity_id)["id"]
    except Exception as exc:
        logger.warning(
            "failed to start a conversation, continuing without persistence: %s", exc
        )
        return None


def _persist_message(
    conversation_id: str | None, entity_id: str, role: str, content: str
) -> None:
    if not conversation_id:
        return
    try:
        ConversationService.add_message(
            conversation_id, entity_id, role=role, content=content
        )
    except Exception as exc:
        logger.warning("failed to persist %s message: %s", role, exc)


@router.post("/query")
def chat_query(req: ChatRequest, current_user: dict = Depends(get_current_user)):
    """Handle one user message end to end.

    Retrieve learnings -> detect intent -> (refuse | persist) -> fetch FAQ source
    -> build the answer. Every external call is fail-open, so a broken
    dependency degrades the answer instead of failing the request.
    """
    # Who this conversation is for: it decides whose personal learnings are
    # loaded and who a new personal learning belongs to. It always comes from
    # the bearer token, so a user can only ever read and write their own.
    entity_id = current_user["id"]
    logger.info("Chat query received: %r (entity_id=%s)", req.query, entity_id)

    # New chat by default; reuse req.conversation_id to continue an older one.
    # Fail-open: a Mongo hiccup here must not take down the chat request.
    conversation_id = _resolve_conversation_id(req.conversation_id, entity_id)
    _persist_message(conversation_id, entity_id, "user", req.query)

    # The conversation we hand to the learnings service: earlier turns (if the
    # frontend sent any) plus the message the user just typed.
    conversation = [
        {"role": m.role, "content": m.content} for m in (req.messages or [])
    ]
    conversation.append({"role": "user", "content": req.query})

    # --- Step 1: load this user's learnings (personal + global) in one call ---
    personal_learnings, global_learnings = learnings_api.list_learnings(entity_id)
    logger.info(
        "Learnings retrieved: %d personal, %d global",
        len(personal_learnings),
        len(global_learnings),
    )

    # --- Step 2: detect intent (uses the learnings to rewrite the query) ---
    intent = intent_service.detect_intent(
        req.query, personal_learnings, global_learnings
    )
    logger.info("Intent detected: %s", intent)

    # --- Step 3: refuse politely if the message is abusive or off-topic ---
    if intent["is_abusive"] or intent["out_of_scope"]:
        logger.info(
            "Refusing message (abusive=%s, out_of_scope=%s)",
            intent["is_abusive"],
            intent["out_of_scope"],
        )
        return _build_response(
            req,
            intent,
            faq_items=[],
            persisted=None,
            learnings=(personal_learnings, global_learnings),
            message=REFUSAL_MESSAGE,
            conversation_id=conversation_id,
            entity_id=entity_id,
        )

    # --- Step 4: persist a learning when the message contains one ---
    persisted = None
    if intent["has_a_learning"]:
        logger.info("Message contains a learning, persisting it")
        persisted = learnings_api.persist(conversation, entity_id=entity_id)
        logger.info("Persist result: %s", persisted)

    # --- Step 5: fetch FAQ source data, only when the answer needs it ---
    faq_items = []
    if intent["needs_source_data"]:
        faq_items = faq_search_service.search_faqs(intent["rewritten_query"])
        logger.info("FAQ search returned %d items", len(faq_items))
    else:
        logger.info("Skipping FAQ search (needs_source_data is false)")

    # --- Step 6: build the answer from the rewritten query + FAQ + learnings ---
    learnings_block = learnings_api.format_block(personal_learnings + global_learnings)
    message = LLMService.synthesize_answer(
        intent["rewritten_query"], faq_items, learnings=learnings_block
    )
    logger.info("Answer built (%d characters)", len(message))

    return _build_response(
        req,
        intent,
        faq_items,
        persisted,
        (personal_learnings, global_learnings),
        message,
        conversation_id=conversation_id,
        entity_id=entity_id,
    )


def _build_response(
    req, intent, faq_items, persisted, learnings, message, conversation_id, entity_id
):
    """Assemble the API response, including fields that make the flow visible.

    Also where the agent's answer gets persisted — the single choke point
    both call sites (refusal and normal path) return through.
    """
    personal_learnings, global_learnings = learnings
    _persist_message(conversation_id, entity_id, "agent", message)
    return {
        "conversation_id": conversation_id,
        "query": req.query,
        "rewritten_query": intent["rewritten_query"],
        "intent": intent,
        "results": faq_items,
        "learnings_used": {
            "personal": len(personal_learnings),
            "global": len(global_learnings),
        },
        "persisted": persisted,
        "message": message,
    }


# -- conversation history (sidebar support) --------------------------------
# Deliberately kept in this same router/file, under the existing /chat
# prefix, rather than a separate /conversations resource: this is read-only
# support data for the chat feature, not a standalone resource of its own.


@router.get("/conversations", response_model=list[ConversationOut])
def list_conversations(current_user: dict = Depends(get_current_user)):
    """This user's conversations, most recently active first — the sidebar list."""
    return ConversationService.list_conversations(current_user["id"])


@router.get(
    "/conversations/{conversation_id}/messages", response_model=list[MessageOut]
)
def get_conversation_messages(
    conversation_id: str, current_user: dict = Depends(get_current_user)
):
    """Full message history for one of the user's own conversations —
    what the sidebar loads when an older conversation is opened."""
    try:
        return ConversationService.get_messages(conversation_id, current_user["id"])
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="conversation not found"
        )
