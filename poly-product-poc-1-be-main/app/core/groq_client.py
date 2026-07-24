"""Shared Groq client helper.

One place to build a Groq client from settings, reused by the LLM synthesis and
the intent detector. Returns None when no key is configured so callers can
degrade gracefully instead of crashing.
"""

from __future__ import annotations

from app.core.config import settings


def get_groq_client():
    """Return a Groq client, or None when GROQ_API_KEY is not set."""
    if not settings.GROQ_API_KEY:
        return None
    from groq import Groq

    return Groq(api_key=settings.GROQ_API_KEY)
