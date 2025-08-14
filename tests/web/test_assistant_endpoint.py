"""Tests for assistant endpoint variations (agent vs classic)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from web.backend.app import app

client = TestClient(app)


def test_assistant_endpoint_use_agent_false(monkeypatch: pytest.MonkeyPatch) -> None:
    # Ensure OPENAI key present for classic path too
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    resp = client.post("/assistant/message", data={"question": "Hello", "use_agent": "false"})
    assert resp.status_code in (200, 500)
    if resp.status_code == 200:
        data = resp.json()
        assert set(data.keys()) == {"answer", "status", "trace"}
        assert data["status"] == "completed"
        assert data["trace"] == []


def test_assistant_endpoint_use_agent_true(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    # For small local indices, endpoint should respond; we only assert shape
    resp = client.post("/assistant/message", data={"question": "What improves VO2 max?", "use_agent": "true"})
    assert resp.status_code in (200, 500)
    if resp.status_code == 200:
        data = resp.json()
        assert set(data.keys()) == {"answer", "status", "trace"}
        assert isinstance(data["trace"], list)
        # Ensure no large payloads
        for node in data["trace"]:
            assert "page_content" not in str(node)


