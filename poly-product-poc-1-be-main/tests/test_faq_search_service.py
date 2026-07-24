"""Tests for the FAQ search steps, including per-step failure handling."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.services import faq_search_service as faq_search


def _match(faq_id: str):
    m = MagicMock()
    m.metadata = {"faq_id": faq_id}
    return m


@pytest.fixture
def stub_steps(monkeypatch):
    """Wire up a working happy path; individual tests override a single step."""
    monkeypatch.setattr(
        faq_search.EmbeddingService,
        "embed_question",
        staticmethod(lambda q: [0.1, 0.2]),
    )
    monkeypatch.setattr(
        faq_search.VectorService, "query", staticmethod(lambda emb: [_match("abc")])
    )
    monkeypatch.setattr(
        faq_search.FAQService,
        "get_by_ids",
        staticmethod(
            lambda ids: [
                {"_id": "abc", "section": "Billing", "question": "Q?", "answer": "A."}
            ]
        ),
    )


def test_happy_path_returns_shaped_items(stub_steps):
    items = faq_search.search_faqs("how do refunds work?")
    assert items == [
        {
            "id": "abc",
            "section": "Billing",
            "question": "Q?",
            "answer": "A.",
            "created_at": None,
            "updated_at": None,
        }
    ]


def test_embedding_failure_returns_empty(stub_steps, monkeypatch):
    def boom(q):
        raise RuntimeError("no OPENAI_API_KEY")

    monkeypatch.setattr(
        faq_search.EmbeddingService, "embed_question", staticmethod(boom)
    )
    assert faq_search.search_faqs("anything") == []


def test_pinecone_failure_returns_empty(stub_steps, monkeypatch):
    def boom(emb):
        raise RuntimeError("401 Invalid API key")

    monkeypatch.setattr(faq_search.VectorService, "query", staticmethod(boom))
    assert faq_search.search_faqs("anything") == []


def test_mongo_failure_returns_empty(stub_steps, monkeypatch):
    def boom(ids):
        raise RuntimeError("mongo unreachable")

    monkeypatch.setattr(faq_search.FAQService, "get_by_ids", staticmethod(boom))
    assert faq_search.search_faqs("anything") == []


def test_logs_each_step(stub_steps, caplog):
    with caplog.at_level("INFO"):
        faq_search.search_faqs("refunds")
    text = caplog.text
    assert "FAQ step 1" in text
    assert "FAQ step 2" in text
    assert "FAQ step 3" in text
