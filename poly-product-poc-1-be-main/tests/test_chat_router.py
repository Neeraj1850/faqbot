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
from app.services.conversation_service import ConversationService


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


def _conversation(conv_id="conv-1", user_id="test-user"):
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    return {"id": conv_id, "user_id": user_id, "created_at": now, "updated_at": now}


def _message(
    msg_id="msg-1", conv_id="conv-1", user_id="test-user", role="user", content="hi"
):
    from datetime import datetime, timezone

    return {
        "id": msg_id,
        "conversation_id": conv_id,
        "user_id": user_id,
        "role": role,
        "content": content,
        "source": "",
        "timestamp": datetime.now(timezone.utc),
    }


@pytest.fixture
def calls():
    return {
        "persist": 0,
        "faq_query": None,
        "synth_query": None,
        "synth_learnings": None,
        "messages": [],
    }


@pytest.fixture
def client(monkeypatch, calls):
    app = FastAPI()
    app.include_router(cr.router)
    from app.dependencies.auth import get_current_user

    app.dependency_overrides[get_current_user] = lambda: {
        "id": "test-user",
        "email": "test@example.com",
    }

    # Default wiring: no learnings, FAQ returns one item.
    monkeypatch.setattr(learnings_api, "list_learnings", lambda entity_id: ([], []))

    # Default conversation wiring: always "creates" conv-default, and records
    # every persisted message without touching real Mongo/bson.
    monkeypatch.setattr(
        ConversationService,
        "create_conversation",
        lambda user_id: {"id": "conv-default", "user_id": user_id},
    )
    monkeypatch.setattr(
        ConversationService, "get_conversation", lambda conversation_id, user_id: None
    )

    def fake_add_message(conversation_id, user_id, role, content, source=""):
        calls["messages"].append(
            {"conversation_id": conversation_id, "role": role, "content": content}
        )
        return {
            "id": "msg-x",
            "conversation_id": conversation_id,
            "user_id": user_id,
            "role": role,
            "content": content,
            "source": source,
        }

    monkeypatch.setattr(ConversationService, "add_message", fake_add_message)

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

    resp = client.post("/chat/query", json={"query": "orig question"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["message"] == "the answer"
    assert body["rewritten_query"] == "rewritten!"
    # The rewritten query — not the original — drives FAQ search and synthesis.
    assert calls["faq_query"] == "rewritten!"
    assert calls["synth_query"] == "rewritten!"
    assert calls["persist"] == 0


def test_entity_id_comes_from_the_logged_in_user(client, monkeypatch):
    monkeypatch.setattr(
        intent_service, "detect_intent", lambda q, p, g: _intent(has_a_learning=True)
    )
    seen = {}

    def fake_list(entity_id):
        seen["listed"] = entity_id
        return ([], [])

    monkeypatch.setattr(learnings_api, "list_learnings", fake_list)

    def fake_persist(messages, entity_id=None):
        seen["persisted"] = entity_id
        return None

    monkeypatch.setattr(learnings_api, "persist", fake_persist)

    resp = client.post("/chat/query", json={"query": "a question"})
    assert resp.status_code == 200
    # The client never sends an entity id; it always comes from the token.
    assert seen["listed"] == "test-user"
    assert seen["persisted"] == "test-user"


@pytest.mark.parametrize("flag", ["is_abusive", "out_of_scope"])
def test_refusal_skips_persist_and_faq(client, monkeypatch, calls, flag):
    monkeypatch.setattr(
        intent_service,
        "detect_intent",
        lambda q, p, g: _intent(**{flag: True, "has_a_learning": True}),
    )

    resp = client.post("/chat/query", json={"query": "bad message"})
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

    resp = client.post("/chat/query", json={"query": "remember: SVGs means savings"})
    assert resp.status_code == 200
    assert calls["persist"] == 1
    assert resp.json()["persisted"]["learning_id"] == "id-1"


def test_skips_faq_when_source_data_not_needed(client, monkeypatch, calls):
    monkeypatch.setattr(
        intent_service,
        "detect_intent",
        lambda q, p, g: _intent(needs_source_data=False),
    )

    resp = client.post("/chat/query", json={"query": "thanks!"})
    assert resp.status_code == 200
    assert calls["faq_query"] is None  # FAQ search never called
    assert resp.json()["results"] == []
    assert resp.json()["message"] == "the answer"


def test_both_scopes_reach_intent_and_prompt(client, monkeypatch, calls):
    monkeypatch.setattr(
        learnings_api,
        "list_learnings",
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

    resp = client.post("/chat/query", json={"query": "a question"})
    assert resp.status_code == 200
    assert len(seen["personal"]) == 1
    assert len(seen["global"]) == 1
    assert resp.json()["learnings_used"] == {"personal": 1, "global": 1}
    # Both scopes must also reach the answer prompt.
    assert "answer in a table" in calls["synth_learnings"]
    assert "fiscal year starts in April" in calls["synth_learnings"]


def test_history_is_included_in_conversation(client, monkeypatch, calls):
    monkeypatch.setattr(
        intent_service, "detect_intent", lambda q, p, g: _intent(has_a_learning=True)
    )
    seen = {}

    def fake_persist(messages, entity_id=None):
        seen["messages"] = messages
        return None

    monkeypatch.setattr(learnings_api, "persist", fake_persist)

    client.post(
        "/chat/query",
        json={
            "query": "and remember that",
            "messages": [{"role": "user", "content": "earlier turn"}],
        },
    )
    # Prior turns plus the current message are sent to the learnings judge.
    assert [m["content"] for m in seen["messages"]] == [
        "earlier turn",
        "and remember that",
    ]


# -- conversation persistence ----------------------------------------------


def test_new_chat_starts_a_conversation_and_saves_both_messages(
    client, monkeypatch, calls
):
    monkeypatch.setattr(intent_service, "detect_intent", lambda q, p, g: _intent())

    resp = client.post("/chat/query", json={"query": "hello there"})

    assert resp.status_code == 200
    assert resp.json()["conversation_id"] == "conv-default"
    assert calls["messages"] == [
        {"conversation_id": "conv-default", "role": "user", "content": "hello there"},
        {"conversation_id": "conv-default", "role": "agent", "content": "the answer"},
    ]


def test_refusal_still_saves_both_messages(client, monkeypatch, calls):
    """Even a refused message is a real turn in the conversation."""
    monkeypatch.setattr(
        intent_service, "detect_intent", lambda q, p, g: _intent(is_abusive=True)
    )

    resp = client.post("/chat/query", json={"query": "bad message"})

    assert resp.status_code == 200
    assert calls["messages"] == [
        {"conversation_id": "conv-default", "role": "user", "content": "bad message"},
        {
            "conversation_id": "conv-default",
            "role": "agent",
            "content": cr.REFUSAL_MESSAGE,
        },
    ]


def test_continuing_an_existing_conversation_reuses_its_id(client, monkeypatch, calls):
    """Passing a real, owned conversation_id must not create a new one."""
    monkeypatch.setattr(intent_service, "detect_intent", lambda q, p, g: _intent())
    monkeypatch.setattr(
        ConversationService,
        "get_conversation",
        lambda conversation_id, user_id: {"id": conversation_id, "user_id": user_id},
    )
    created = {"count": 0}

    def fail_if_called(user_id):
        created["count"] += 1
        return {"id": "should-not-be-used", "user_id": user_id}

    monkeypatch.setattr(ConversationService, "create_conversation", fail_if_called)

    resp = client.post(
        "/chat/query", json={"query": "continuing", "conversation_id": "old-conv-1"}
    )

    assert resp.status_code == 200
    assert resp.json()["conversation_id"] == "old-conv-1"
    assert created["count"] == 0  # reused, never created a new conversation
    assert calls["messages"][0]["conversation_id"] == "old-conv-1"


def test_unknown_conversation_id_falls_back_to_a_new_conversation(
    client, monkeypatch, calls
):
    """A stale/foreign conversation_id must not break the chat request —
    it just starts a fresh conversation instead (fail-open)."""
    monkeypatch.setattr(intent_service, "detect_intent", lambda q, p, g: _intent())
    # Default fixture wiring already makes get_conversation return None
    # (not found) and create_conversation return conv-default.

    resp = client.post(
        "/chat/query",
        json={"query": "hi", "conversation_id": "someone-elses-conversation"},
    )

    assert resp.status_code == 200
    assert resp.json()["conversation_id"] == "conv-default"


def test_chat_still_works_when_conversation_persistence_is_down(
    client, monkeypatch, calls
):
    """Mongo being unreachable must degrade persistence, not the chat answer
    — matching this router's stated fail-open philosophy for every dependency."""
    monkeypatch.setattr(intent_service, "detect_intent", lambda q, p, g: _intent())

    def boom(user_id):
        raise ConnectionError("mongo is down")

    monkeypatch.setattr(ConversationService, "create_conversation", boom)

    resp = client.post("/chat/query", json={"query": "hello"})

    assert resp.status_code == 200
    assert resp.json()["message"] == "the answer"
    assert resp.json()["conversation_id"] is None
    assert calls["messages"] == []  # nothing to persist to without a conversation


# -- conversation history endpoints (sidebar support) ----------------------


def test_list_conversations_returns_this_users_conversations(client, monkeypatch):
    convs = [_conversation(conv_id="c1"), _conversation(conv_id="c2")]
    seen = {}

    def fake_list(user_id):
        seen["user_id"] = user_id
        return convs

    monkeypatch.setattr(ConversationService, "list_conversations", fake_list)

    resp = client.get("/chat/conversations")

    assert resp.status_code == 200
    body = resp.json()
    assert [c["id"] for c in body] == ["c1", "c2"]
    assert seen["user_id"] == "test-user"


def test_get_conversation_messages_returns_history_in_order(client, monkeypatch):
    history = [
        _message(msg_id="1", role="user", content="first"),
        _message(msg_id="2", role="agent", content="second"),
    ]
    monkeypatch.setattr(
        ConversationService, "get_messages", lambda conversation_id, user_id: history
    )

    resp = client.get("/chat/conversations/conv-1/messages")

    assert resp.status_code == 200
    body = resp.json()
    assert [m["content"] for m in body] == ["first", "second"]


def test_get_conversation_messages_scoped_to_the_logged_in_user(client, monkeypatch):
    """A conversation_id in the URL is only ever resolved against the
    caller's own user_id (from the token) — this is what makes 'continuing
    an older conversation' safe: you can't continue someone else's."""
    seen = {}

    def fake_get(conversation_id, user_id):
        seen.update(conversation_id=conversation_id, user_id=user_id)
        return [_message(conv_id=conversation_id)]

    monkeypatch.setattr(ConversationService, "get_messages", fake_get)

    resp = client.get("/chat/conversations/an-older-conversation/messages")

    assert resp.status_code == 200
    assert seen == {"conversation_id": "an-older-conversation", "user_id": "test-user"}


def test_get_conversation_messages_for_unknown_conversation_is_404(client, monkeypatch):
    def fake_get(conversation_id, user_id):
        raise ValueError("conversation not found")

    monkeypatch.setattr(ConversationService, "get_messages", fake_get)

    resp = client.get("/chat/conversations/does-not-exist/messages")

    assert resp.status_code == 404
