"""Tests for the Groq intent detector — 5-field parsing + fail-safe defaults."""

from __future__ import annotations

import json
import sys
import types
from unittest.mock import MagicMock


from app.core.config import settings
from app.services import intent_service


def _install_fake_groq(monkeypatch, content: str):
    """Install a fake `groq` module whose client returns `content` as the answer."""
    completion = MagicMock()
    completion.choices = [MagicMock(message=MagicMock(content=content))]
    client = MagicMock()
    client.chat.completions.create.return_value = completion

    fake = types.ModuleType("groq")
    fake.Groq = MagicMock(return_value=client)  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "groq", fake)
    monkeypatch.setattr(settings, "GROQ_API_KEY", "test-key")
    return client


def test_parses_all_five_fields(monkeypatch):
    _install_fake_groq(
        monkeypatch,
        json.dumps(
            {
                "needs_source_data": True,
                "is_abusive": False,
                "out_of_scope": False,
                "rewritten_query": "HOW MANY savings ACCOUNTS WERE OPENED LAST MONTH",
                "has_a_learning": False,
                "learning_reason": "this is a question, not a teaching statement",
            }
        ),
    )
    result = intent_service.detect_intent(
        "HOW MANY SVGS ACCOUNTS WERE OPENED LAST MONTH",
        personal_learnings=[
            {"context": "user says SVGs", "content": "SVGs means savings"}
        ],
        global_learnings=[],
    )
    assert result["needs_source_data"] is True
    assert result["is_abusive"] is False
    assert result["out_of_scope"] is False
    assert result["has_a_learning"] is False
    assert "savings" in result["rewritten_query"]
    assert result["learning_reason"] == "this is a question, not a teaching statement"


def test_learnings_are_sent_in_the_prompt(monkeypatch):
    client = _install_fake_groq(
        monkeypatch,
        json.dumps(
            {
                "needs_source_data": True,
                "is_abusive": False,
                "out_of_scope": False,
                "rewritten_query": "q",
                "has_a_learning": False,
            }
        ),
    )
    intent_service.detect_intent(
        "how many SVGs?",
        personal_learnings=[
            {"context": "user says SVGs", "content": "SVGs means savings"}
        ],
        global_learnings=[
            {"context": "account code", "content": "code is #UnoSavings"}
        ],
    )
    sent = client.chat.completions.create.call_args.kwargs["messages"][1]["content"]
    assert "SVGs means savings" in sent
    assert "#UnoSavings" in sent


def test_abusive_and_out_of_scope_flags(monkeypatch):
    _install_fake_groq(
        monkeypatch,
        json.dumps(
            {
                "needs_source_data": False,
                "is_abusive": True,
                "out_of_scope": True,
                "rewritten_query": "",
                "has_a_learning": False,
            }
        ),
    )
    result = intent_service.detect_intent("something rude")
    assert result["is_abusive"] is True
    assert result["out_of_scope"] is True
    # Empty rewritten_query falls back to the original message.
    assert result["rewritten_query"] == "something rude"


def test_defaults_when_groq_not_configured(monkeypatch):
    monkeypatch.setattr(settings, "GROQ_API_KEY", None)
    result = intent_service.detect_intent("what is the refund policy?")
    assert result == {
        "needs_source_data": True,
        "is_abusive": False,
        "out_of_scope": False,
        "rewritten_query": "what is the refund policy?",
        "has_a_learning": False,
        "learning_reason": "intent detection unavailable",
    }


def test_prompt_states_the_question_and_correction_rules():
    """Guard the wording that drives has_a_learning.

    The model's own behaviour can't be unit-tested against a fake client, so this
    protects the two rules that fixed questions being treated as learnings.
    """
    prompt = intent_service._SYSTEM_PROMPT
    assert "A QUESTION IS NEVER A LEARNING" in prompt
    assert "EXCEPTION" in prompt  # corrections must still be persisted
    assert "already known" in prompt


def test_defaults_on_bad_json(monkeypatch):
    _install_fake_groq(monkeypatch, "not json at all")
    result = intent_service.detect_intent("a question")
    # Must not refuse the user just because the model misbehaved.
    assert result["is_abusive"] is False
    assert result["out_of_scope"] is False
    assert result["needs_source_data"] is True
    assert result["rewritten_query"] == "a question"
    assert result["learning_reason"] == "intent detection unavailable"
