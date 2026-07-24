"""Router tests for the single-call chat flow.

Covers each branch of the design: refusal, persist, skipping the FAQ fetch, and
the normal path where the rewritten query is what reaches the downstream steps.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import chat_router as cr
from app.services import learnings_api, intent_service, faq_search_service


def _intent(**overrides):
    base = {
        "needs_source_data": True,
        "is_abusive": False,
        "out_of_scope": False,
        "rewritten_query": "rewritten!",
        "has_a_learning": False,
        "learning_reason": "",
    }
    base.update(overrides)
    return base


@pytest.fixture
def calls():
    return {"persist": 0, "faq_query": None, "synth_query": None, "synth_learnings": None}


@pytest.fixture
def client(monkeypatch, calls):
    app = FastAPI()
    app.include_router(cr.router)
    from app.dependencies.api_key_auth import require_api_key

    app.dependency_overrides[require_api_key] = lambda: True

    # Default wiring: no learnings, FAQ returns one item.
    monkeypatch.setattr(learnings_api, "list_learnings", lambda entity_id: ([], []))

    def fake_persist(messages, entity_id=None):
        calls["persist"] += 1
        return {"decision": "persisted", "verdict": "new", "learning_id": "id-1"}

    monkeypatch.setattr(learnings_api, "persist", fake_persist)

    def fake_search(query):
        calls["faq_query"] = query
        return [{"id": "1", "section": "S", "question": "Q", "answer": "A"}]

    monkeypatch.setattr(faq_search_service, "search_faqs", fake_search)

    def fake_synth(query, faqs, learnings=""):
        calls["synth_query"] = query
        calls["synth_learnings"] = learnings
        return "the answer"

    monkeypatch.setattr(cr.LLMService, "synthesize_answer", staticmethod(fake_synth))
    return TestClient(app)


def test_normal_path_uses_rewritten_query(client, monkeypatch, calls):
    monkeypatch.setattr(intent_service, "detect_intent", lambda q, p, g: _intent())

    resp = client.post("/chat/query", json={"query": "orig question", "entity_id": "acme"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["message"] == "the answer"
    assert body["rewritten_query"] == "rewritten!"
    # The rewritten query — not the original — drives FAQ search and synthesis.
    assert calls["faq_query"] == "rewritten!"
    assert calls["synth_query"] == "rewritten!"
    assert calls["persist"] == 0


def test_entity_id_is_required(client):
    resp = client.post("/chat/query", json={"query": "no entity id here"})
    assert resp.status_code == 422


@pytest.mark.parametrize("flag", ["is_abusive", "out_of_scope"])
def test_refusal_skips_persist_and_faq(client, monkeypatch, calls, flag):
    monkeypatch.setattr(
        intent_service, "detect_intent",
        lambda q, p, g: _intent(**{flag: True, "has_a_learning": True}),
    )

    resp = client.post("/chat/query", json={"query": "bad message", "entity_id": "acme"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["message"] == cr.REFUSAL_MESSAGE
    assert body["results"] == []
    assert body["persisted"] is None
    # A refusal must not store anything or hit the FAQ database.
    assert calls["persist"] == 0
    assert calls["faq_query"] is None


def test_persists_when_message_has_a_learning(client, monkeypatch, calls):
    monkeypatch.setattr(
        intent_service, "detect_intent", lambda q, p, g: _intent(has_a_learning=True)
    )

    resp = client.post("/chat/query", json={"query": "remember: SVGs means savings",
                                            "entity_id": "acme"})
    assert resp.status_code == 200
    assert calls["persist"] == 1
    assert resp.json()["persisted"]["learning_id"] == "id-1"


def test_skips_faq_when_source_data_not_needed(client, monkeypatch, calls):
    monkeypatch.setattr(
        intent_service, "detect_intent", lambda q, p, g: _intent(needs_source_data=False)
    )

    resp = client.post("/chat/query", json={"query": "thanks!", "entity_id": "acme"})
    assert resp.status_code == 200
    assert calls["faq_query"] is None  # FAQ search never called
    assert resp.json()["results"] == []
    assert resp.json()["message"] == "the answer"


def test_both_scopes_reach_intent_and_prompt(client, monkeypatch, calls):
    monkeypatch.setattr(
        learnings_api, "list_learnings",
        lambda entity_id: (
            [{"context": "c1", "content": "answer in a table"}],
            [{"context": "c2", "content": "fiscal year starts in April"}],
        ),
    )
    seen = {}

    def fake_detect(query, personal, global_):
        seen["personal"] = personal
        seen["global"] = global_
        return _intent()

    monkeypatch.setattr(intent_service, "detect_intent", fake_detect)

    resp = client.post("/chat/query", json={"query": "a question", "entity_id": "acme"})
    assert resp.status_code == 200
    assert len(seen["personal"]) == 1
    assert len(seen["global"]) == 1
    assert resp.json()["learnings_used"] == {"personal": 1, "global": 1}
    # Both scopes must also reach the answer prompt.
    assert "answer in a table" in calls["synth_learnings"]
    assert "fiscal year starts in April" in calls["synth_learnings"]


def test_history_is_included_in_conversation(client, monkeypatch, calls):
    monkeypatch.setattr(intent_service, "detect_intent", lambda q, p, g: _intent(has_a_learning=True))
    seen = {}

    def fake_persist(messages, entity_id=None):
        seen["messages"] = messages
        return None

    monkeypatch.setattr(learnings_api, "persist", fake_persist)

    client.post("/chat/query", json={
        "query": "and remember that",
        "entity_id": "acme",
        "messages": [{"role": "user", "content": "earlier turn"}],
    })
    # Prior turns plus the current message are sent to the learnings judge.
    assert [m["content"] for m in seen["messages"]] == ["earlier turn", "and remember that"]
