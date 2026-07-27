"""Talk to the polynomial-learnings service over plain HTTP.

We call the learnings REST API directly with ``httpx`` (no SDK) so the code is
easy to follow: one function == one HTTP request. Everything here is
"fail-open" — if the learnings service is down or misconfigured, these functions
return an empty result instead of raising, so the chatbot keeps working.

The learnings service exposes (see the polynomial-learnings repo):
  GET  {BASE}/v1/agents/{agent_id}/learnings?entity_id=...  -> personal + global
  POST {BASE}/v1/agents/{agent_id}/persist                  -> judges + stores a learning

We list learnings rather than using the service's /retrieve search on purpose:
/retrieve is relevance-ranked and would drop standing preferences (e.g. "always
answer me in a table") that don't match the current question semantically.
"""

from __future__ import annotations

import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


def is_enabled() -> bool:
    """True when a learnings service URL is configured."""
    return bool(settings.LEARNINGS_BASE_URL)


def _url(path: str) -> str:
    """Build a full URL like http://host/v1/agents/faqbot/learnings."""
    base = settings.LEARNINGS_BASE_URL.rstrip("/")
    return f"{base}/v1/agents/{settings.LEARNINGS_AGENT_ID}{path}"


def list_learnings(entity_id: str) -> tuple[list[dict], list[dict]]:
    """Load this entity's personal learnings and the agent's global learnings.

    One request returns both sets. Returns ([], []) when the integration is
    disabled or the service is unreachable, so the caller can carry on.
    """
    if not is_enabled():
        return [], []

    params = {"entity_id": entity_id, "limit": settings.LEARNINGS_LIST_LIMIT}
    try:
        resp = httpx.get(_url("/learnings"), params=params, timeout=settings.LEARNINGS_TIMEOUT)
        resp.raise_for_status()
        body = resp.json()
        return body.get("personal", []), body.get("global", [])
    except Exception as exc:  # network error, timeout, non-2xx — all non-fatal
        logger.warning("learnings list failed, continuing without: %s", exc)
        return [], []


def format_block(learnings: list[dict]) -> str:
    """Render learnings as a short block to drop into the LLM prompt.

    Learnings are ordered newest first and ALL of them are included. The header
    tells the model to treat the most recent preference as top priority while
    still honouring every other preference that can coexist with it, and to skip
    an older one only when it directly conflicts with a more recent one.
    ``created_at`` is an ISO-8601 UTC string, so a plain reverse sort on it is
    chronological; items without a date sort to the bottom.
    """
    if not learnings:
        return ""

    newest_first = sorted(
        learnings,
        key=lambda item: item.get("created_at", ""),
        reverse=True,
    )

    lines = [
        "Apply the following user preferences, listed most recent first. Treat "
        "the most recent one as the top priority, and also honour every other "
        "preference that can reasonably coexist with it and is relevant to the "
        "question. Only skip an older preference when it directly conflicts with "
        "a more recent one (for example two mutually exclusive response "
        "formats); in that case follow the more recent one:"
    ]
    for item in newest_first:
        # Show just the date (not the time) as a light recency hint; fall back
        # to no prefix when the learning has no timestamp.
        created_at = item.get("created_at", "")
        date_hint = f"({created_at[:10]}) " if created_at else ""
        lines.append(f"- {date_hint}When {item['context']}: {item['content']}")
    return "\n".join(lines)


def persist(messages: list[dict], entity_id: str | None = None) -> dict | None:
    """Send a conversation to the learnings service to be judged and stored.

    The server runs its own judge and writes the learning if warranted. Returns
    the PersistResult JSON on success, or None when disabled / on any error
    (including 503 when the server has no judge configured).
    """
    if not is_enabled():
        return None

    payload = {"messages": messages, "entity_id": entity_id}
    try:
        resp = httpx.post(_url("/persist"), json=payload, timeout=settings.LEARNINGS_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("learnings persist failed: %s", exc)
        return None
