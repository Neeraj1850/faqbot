"""Unit tests for ConversationService's title-on-first-message logic.

Real service code, fake in-memory collections — no real bson/pymongo (this
project's test env doesn't have them installed; conftest.py stubs
bson.ObjectId with a bare MagicMock, and separate MagicMock() calls aren't
equal to each other, which breaks any code path that round-trips an id
through ObjectId(...) more than once). This file sidesteps that by patching
ConversationService's ObjectId to the identity function, so the fake
collections below can match on plain string ids.
"""

from __future__ import annotations

import itertools

import pytest

from app.services import conversation_service as cs


class _InsertResult:
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id


class _FakeCursor(list):
    def sort(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self


class _FakeCollection:
    def __init__(self):
        self._docs: dict[str, dict] = {}
        self._counter = itertools.count(1)

    def insert_one(self, doc):
        doc_id = f"id-{next(self._counter)}"
        doc["_id"] = doc_id
        self._docs[doc_id] = doc
        return _InsertResult(doc_id)

    def find_one(self, filt):
        for doc in self._docs.values():
            if all(doc.get(k) == v for k, v in filt.items()):
                return doc
        return None

    def update_one(self, filt, update):
        doc = self.find_one(filt)
        if doc is not None:
            doc.update(update.get("$set", {}))

    def find(self, filt):
        return _FakeCursor(
            d for d in self._docs.values() if all(d.get(k) == v for k, v in filt.items())
        )


@pytest.fixture(autouse=True)
def fake_mongo(monkeypatch):
    monkeypatch.setattr(cs, "ObjectId", lambda x: x)
    monkeypatch.setattr(cs, "conversation_collection", _FakeCollection())
    monkeypatch.setattr(cs, "message_collection", _FakeCollection())


def test_first_user_message_becomes_the_title():
    conv = cs.ConversationService.create_conversation("alice")

    cs.ConversationService.add_message(conv["id"], "alice", "user", "how do I reset my password?")

    updated = cs.ConversationService.get_conversation(conv["id"], "alice")
    assert updated["title"] == "how do I reset my password?"


def test_title_is_not_overwritten_by_later_messages():
    conv = cs.ConversationService.create_conversation("alice")
    cs.ConversationService.add_message(conv["id"], "alice", "user", "first message")
    cs.ConversationService.add_message(conv["id"], "alice", "agent", "an answer")
    cs.ConversationService.add_message(
        conv["id"], "alice", "user", "a completely different second question"
    )

    updated = cs.ConversationService.get_conversation(conv["id"], "alice")
    assert updated["title"] == "first message"


def test_title_is_truncated_to_60_chars():
    conv = cs.ConversationService.create_conversation("alice")
    long_message = "x" * 100

    cs.ConversationService.add_message(conv["id"], "alice", "user", long_message)

    updated = cs.ConversationService.get_conversation(conv["id"], "alice")
    assert updated["title"] == "x" * 60


def test_agent_message_alone_does_not_set_a_title():
    conv = cs.ConversationService.create_conversation("alice")

    cs.ConversationService.add_message(conv["id"], "alice", "agent", "hello, how can I help?")

    updated = cs.ConversationService.get_conversation(conv["id"], "alice")
    assert updated["title"] is None


def test_new_conversation_has_no_title():
    conv = cs.ConversationService.create_conversation("alice")
    assert conv["title"] is None
