"""Tests for the direct-HTTP learnings client, incl. the fail-open contract."""

from __future__ import annotations

import httpx

from app.services import learnings_api


def _patch_get(monkeypatch, handler):
    """Route httpx.get through a MockTransport running `handler`."""
    transport = httpx.MockTransport(handler)

    def fake_get(url, params=None, timeout=None):
        with httpx.Client(transport=transport) as client:
            return client.get(url, params=params)

    monkeypatch.setattr(learnings_api.httpx, "get", fake_get)


def _patch_post(monkeypatch, handler):
    """Route httpx.post through a MockTransport running `handler`."""
    transport = httpx.MockTransport(handler)

    def fake_post(url, json=None, timeout=None):
        with httpx.Client(transport=transport) as client:
            return client.post(url, json=json)

    monkeypatch.setattr(learnings_api.httpx, "post", fake_post)


# -- list_learnings --------------------------------------------------------


def test_list_learnings_returns_both_scopes(monkeypatch):
    def handler(request):
        assert request.url.path == "/v1/agents/faqbot/learnings"
        assert request.url.params["entity_id"] == "acme"
        return httpx.Response(
            200,
            json={
                "personal": [
                    {"context": "user prefers tables", "content": "answer in a table"}
                ],
                "global": [{"context": "fiscal year", "content": "starts in April"}],
            },
        )

    _patch_get(monkeypatch, handler)
    personal, global_ = learnings_api.list_learnings("acme")
    assert personal[0]["content"] == "answer in a table"
    assert global_[0]["content"] == "starts in April"


def test_list_learnings_fails_open_on_error(monkeypatch):
    def handler(request):
        raise httpx.ConnectError("boom", request=request)

    _patch_get(monkeypatch, handler)
    assert learnings_api.list_learnings("acme") == ([], [])


def test_list_learnings_fails_open_on_non_2xx(monkeypatch):
    def handler(request):
        return httpx.Response(500, json={"detail": "kaboom"})

    _patch_get(monkeypatch, handler)
    assert learnings_api.list_learnings("acme") == ([], [])


def test_list_learnings_noop_when_disabled(monkeypatch):
    monkeypatch.setattr(learnings_api, "is_enabled", lambda: False)
    assert learnings_api.list_learnings("acme") == ([], [])


# -- format_block ----------------------------------------------------------


def test_format_block_renders_learnings():
    block = learnings_api.format_block(
        [
            {"context": "user asks about refunds", "content": "refunds take 5-7 days"},
        ]
    )
    assert "Relevant learnings from past interactions:" in block
    assert "refunds take 5-7 days" in block


def test_format_block_empty():
    assert learnings_api.format_block([]) == ""


# -- persist ---------------------------------------------------------------


def test_persist_returns_result_on_success(monkeypatch):
    def handler(request):
        assert request.url.path == "/v1/agents/faqbot/persist"
        return httpx.Response(
            200,
            json={"decision": "persisted", "verdict": "new", "learning_id": "abc-123"},
        )

    _patch_post(monkeypatch, handler)
    result = learnings_api.persist(
        [{"role": "user", "content": "a correction"}], entity_id="acme"
    )
    assert result == {
        "decision": "persisted",
        "verdict": "new",
        "learning_id": "abc-123",
    }


def test_persist_maps_error_to_none(monkeypatch):
    def handler(request):
        return httpx.Response(503, json={"detail": "no judge configured"})

    _patch_post(monkeypatch, handler)
    assert (
        learnings_api.persist([{"role": "user", "content": "x"}], entity_id="acme")
        is None
    )


def test_persist_noop_when_disabled(monkeypatch):
    monkeypatch.setattr(learnings_api, "is_enabled", lambda: False)
    assert learnings_api.persist([{"role": "user", "content": "x"}]) is None
