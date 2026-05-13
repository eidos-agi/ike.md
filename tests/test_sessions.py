"""Tests for session management helpers."""

import json
import os

import pytest

from docket_md.files import (
    load_sessions,
    save_sessions,
    add_session,
    add_session_event,
)


class TestSessions:
    def test_load_sessions_missing_file(self, tmp_path):
        result = load_sessions(str(tmp_path))
        assert result == {"sessions": []}

    def test_save_load_roundtrip(self, tmp_path):
        os.makedirs(tmp_path / ".docket", exist_ok=True)
        data = {"sessions": [{"id": "abc", "status": "active"}]}
        save_sessions(str(tmp_path), data)
        loaded = load_sessions(str(tmp_path))
        assert loaded == data

    def test_add_session_new(self, tmp_path):
        os.makedirs(tmp_path / ".docket", exist_ok=True)
        result = add_session(str(tmp_path), "sess-1", "/tmp/sess-1.jsonl", "proj-1")
        assert result is True
        data = load_sessions(str(tmp_path))
        assert len(data["sessions"]) == 1
        s = data["sessions"][0]
        assert s["id"] == "sess-1"
        assert s["status"] == "active"
        assert s["jsonl"] == "/tmp/sess-1.jsonl"
        assert s["project_id"] == "proj-1"
        assert s["events"] == []
        assert "first_seen" in s
        assert "last_activity" in s

    def test_add_session_duplicate(self, tmp_path):
        os.makedirs(tmp_path / ".docket", exist_ok=True)
        add_session(str(tmp_path), "sess-1", "/tmp/sess-1.jsonl", "proj-1")
        result = add_session(str(tmp_path), "sess-1", "/tmp/other.jsonl", "proj-2")
        assert result is False
        data = load_sessions(str(tmp_path))
        assert len(data["sessions"]) == 1

    def test_add_session_event(self, tmp_path):
        os.makedirs(tmp_path / ".docket", exist_ok=True)
        add_session(str(tmp_path), "sess-1", "/tmp/sess-1.jsonl", "proj-1")
        event = {"type": "tool_use", "tool": "read_file"}
        result = add_session_event(str(tmp_path), "sess-1", event)
        assert result is True
        data = load_sessions(str(tmp_path))
        s = data["sessions"][0]
        assert len(s["events"]) == 1
        assert s["events"][0] == event

    def test_add_session_event_missing_session(self, tmp_path):
        os.makedirs(tmp_path / ".docket", exist_ok=True)
        result = add_session_event(str(tmp_path), "nonexistent", {"type": "test"})
        assert result is False
