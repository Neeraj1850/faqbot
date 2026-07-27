import logging

from fastapi import APIRouter, Depends
from app.services.llm_service import LLMService
from app.services import (
    learnings_api,
    intent_service,
    faq_search_service,
)
from pydantic import BaseModel
from app.dependencies.auth import get_current_user

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/chat")

# Shown when the message is abusive or outside what this bot covers.
REFUSAL_MESSAGE = (
    "I'm sorry, but I can't help with that. I can answer questions about our "
    "products and services — feel free to ask me one of those."
)

# Shown when the user only teaches the bot something (a preference or fact)
# without asking a question, so we confirm instead of trying to answer.
LEARNING_ACK_MESSAGE = "Got it — I'll keep that in mind for my answers."


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    query: str
    # Optional earlier turns from the chatbox, giving the learning judge context.
    messages: list[Message] | None = None


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

    # The conversation we hand to the learnings service: earlier turns (if the
    # frontend sent any) plus the message the user just typed.
    conversation = [{"role": m.role, "content": m.content} for m in (req.messages or [])]
    conversation.append({"role": "user", "content": req.query})

    # --- Step 1: load this user's learnings (personal + global) in one call ---
    personal_learnings, global_learnings = learnings_api.list_learnings(entity_id)
    logger.info(
        "Learnings retrieved: %d personal, %d global",
        len(personal_learnings),
        len(global_learnings),
    )

    # --- Step 2: detect intent (uses the learnings to rewrite the query) ---
    intent = intent_service.detect_intent(req.query, personal_learnings, global_learnings)
    logger.info("Intent detected: %s", intent)

    # --- Step 3: refuse politely if the message is abusive or off-topic ---
    if intent["is_abusive"] or intent["out_of_scope"]:
        logger.info("Refusing message (abusive=%s, out_of_scope=%s)",
                    intent["is_abusive"], intent["out_of_scope"])
        return _build_response(req, intent, faq_items=[], persisted=None,
                               learnings=(personal_learnings, global_learnings),
                               message=REFUSAL_MESSAGE)

    # --- Step 4: persist a learning when the message contains one ---
    persisted = None
    if intent["has_a_learning"]:
        logger.info("Message contains a learning, persisting it")
        persisted = learnings_api.persist(conversation, entity_id=entity_id)
        logger.info("Persist result: %s", persisted)

    # When the message only teaches something (a preference or fact) and asks
    # nothing, acknowledge it instead of trying to answer from the FAQ — that
    # path would wrongly say "I don't have that information" for a statement.
    if intent["has_a_learning"] and not intent["needs_source_data"]:
        return _build_response(req, intent, faq_items=[], persisted=persisted,
                               learnings=(personal_learnings, global_learnings),
                               message=LEARNING_ACK_MESSAGE)

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

    return _build_response(req, intent, faq_items, persisted,
                           (personal_learnings, global_learnings), message)


def _build_response(req, intent, faq_items, persisted, learnings, message):
    """Assemble the API response, including fields that make the flow visible."""
    personal_learnings, global_learnings = learnings
    return {
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
