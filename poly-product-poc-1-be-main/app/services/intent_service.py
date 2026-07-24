"""Detect the intent of a user message using a Groq model.

This is the "Detect Intent" step in the system design. It runs *after* we have
retrieved the user's learnings, so the model can use them to rewrite the query
into something better for searching the FAQ database. For example:

    user_query        : "HOW MANY SVGS ACCOUNTS WERE OPENED LAST MONTH"
    personal_learnings: "when I say SVGs I mean savings"
    global_learnings  : "savings accounts code is #UnoSavings"
    -> rewritten_query: "HOW MANY savings ACCOUNTS WERE OPENED LAST MONTH,
                         with accountCode as #UnoSavings"

One Groq call returns all five decisions the chat flow needs.
"""

from __future__ import annotations

import json
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You analyse a user's message for a FAQ chatbot and reply with ONLY JSON.

Use the provided learnings to understand the user's own words: they may explain
abbreviations, jargon, codes, or preferences. Apply them when rewriting the query.

Return exactly this JSON shape:
{
  "needs_source_data": true or false,
  "is_abusive": true or false,
  "out_of_scope": true or false,
  "rewritten_query": "a clearer, expanded version of the user's question",
  "has_a_learning": true or false,
  "learning_reason": "one short sentence explaining the has_a_learning decision"
}

Field meanings:
- needs_source_data: true if answering requires looking up the FAQ knowledge base.
  false for greetings, thanks, or messages that only state a preference/fact.
- is_abusive: true if the message is offensive, hateful, or harassing.
- out_of_scope: true if the message is unrelated to the product/FAQ domain.
- rewritten_query: expand abbreviations and jargon using the learnings. If no
  rewrite is needed, repeat the original question.

- has_a_learning: judge ONLY the user's latest message, using these rules:
  * A QUESTION IS NEVER A LEARNING, even when it asks about a fact. Asking
    "what is X?" is not teaching X. Answer false for every question.
  * Set true only when the user is TELLING you something to remember:
    correcting you, stating a preference, or teaching a new fact.
  * Set false if the message only restates something already present in the
    personal_learnings or global_learnings listed above — it is already known.
  * EXCEPTION: if the message changes, corrects, or contradicts an existing
    learning, set true. Never suppress an update as "already known".

  Examples:
    "What is the support email?"                -> false (a question)
    "Our support email is help@acme.example"    -> true  (teaching a fact)
    "Our support email is help@acme.example"    -> false (if already listed above)
    "Actually the support email is now x@y.com" -> true  (corrects a learning)
    "Always answer me in a table"               -> true  (a stated preference)

- learning_reason: a short sentence saying why has_a_learning is true or false.
"""


def _format_learnings(learnings: list[dict]) -> str:
    """Render a learning list as simple bullet lines for the prompt."""
    if not learnings:
        return "(none)"
    lines = []
    for item in learnings:
        lines.append(f"- {item.get('context', '')}: {item.get('content', '')}")
    return "\n".join(lines)


def _default_intent(query: str) -> dict:
    """Safe fallback: behave like a normal question, don't refuse, don't persist."""
    return {
        "needs_source_data": True,
        "is_abusive": False,
        "out_of_scope": False,
        "rewritten_query": query,
        "has_a_learning": False,
        "learning_reason": "intent detection unavailable",
    }


def detect_intent(
    query: str,
    personal_learnings: list[dict] | None = None,
    global_learnings: list[dict] | None = None,
) -> dict:
    """Return the five intent fields for the user's message.

    Falls back to ``_default_intent`` whenever Groq isn't configured or the call
    fails, so the chat keeps working instead of wrongly refusing the user.
    """
    from app.core.groq_client import get_groq_client

    client = get_groq_client()
    if client is None:
        logger.warning("Groq not configured, using default intent")
        return _default_intent(query)

    user_content = (
        f"user_query: {query}\n"
        f"personal_learnings:\n{_format_learnings(personal_learnings or [])}\n"
        f"global_learnings:\n{_format_learnings(global_learnings or [])}"
    )

    try:
        completion = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.0,
            response_format={"type": "json_object"},
        )
        answer = json.loads(completion.choices[0].message.content)
    except Exception as exc:  # missing dep, network, bad JSON — all non-fatal
        logger.warning("Intent detection failed, using default intent: %s", exc)
        return _default_intent(query)

    # Normalise every field so callers never see a missing key or odd type.
    rewritten = str(answer.get("rewritten_query") or "").strip()
    return {
        "needs_source_data": bool(answer.get("needs_source_data", True)),
        "is_abusive": bool(answer.get("is_abusive", False)),
        "out_of_scope": bool(answer.get("out_of_scope", False)),
        "rewritten_query": rewritten or query,
        "has_a_learning": bool(answer.get("has_a_learning", False)),
        "learning_reason": str(answer.get("learning_reason", "")),
    }
