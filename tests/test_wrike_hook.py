"""Tests for the optional Wrdocket hook."""

import os
from unittest.mock import MagicMock, patch

from docket_md.hooks.wrike_hook import WrikeHook, get_hook


class TestGetHook:
    def test_disabled_returns_none(self):
        assert get_hook({}) is None
        assert get_hook({"wrike": {"enabled": False}}) is None

    def test_no_token_returns_none(self, monkeypatch):
        monkeypatch.delenv("WRDOCKET_ACCESS_TOKEN", raising=False)
        assert get_hook({"wrike": {"enabled": True}}) is None

    def test_enabled_with_token(self, monkeypatch):
        monkeypatch.setenv("WRDOCKET_ACCESS_TOKEN", "test-token")
        hook = get_hook({"wrike": {"enabled": True}})
        assert hook is not None
        assert isinstance(hook, WrikeHook)


class TestOnProjectSet:
    def test_finds_existing_task(self, monkeypatch):
        monkeypatch.setenv("WRDOCKET_ACCESS_TOKEN", "test-token")
        hook = WrikeHook("test-token")

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": [{"id": "TASK123", "title": "My Project"}]
        }
        mock_resp.raise_for_status = MagicMock()
        hook._http = MagicMock()
        hook._http.get.return_value = mock_resp

        result = hook.on_project_set("My Project", "FOLDER1")
        assert result == "TASK123"

    def test_creates_new_when_not_found(self, monkeypatch):
        monkeypatch.setenv("WRDOCKET_ACCESS_TOKEN", "test-token")
        hook = WrikeHook("test-token")

        # Search returns empty
        search_resp = MagicMock()
        search_resp.json.return_value = {"data": []}
        search_resp.raise_for_status = MagicMock()

        # Create returns new task
        create_resp = MagicMock()
        create_resp.json.return_value = {"data": [{"id": "NEWTASK"}]}
        create_resp.raise_for_status = MagicMock()

        hook._http = MagicMock()
        hook._http.get.return_value = search_resp
        hook._http.post.return_value = create_resp

        result = hook.on_project_set("New Project", "FOLDER1")
        assert result == "NEWTASK"


class TestOnBookmark:
    def test_posts_comment(self, monkeypatch):
        monkeypatch.setenv("WRDOCKET_ACCESS_TOKEN", "test-token")
        hook = WrikeHook("test-token")

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": [{"id": "COMMENT1"}]}
        mock_resp.raise_for_status = MagicMock()
        hook._http = MagicMock()
        hook._http.post.return_value = mock_resp

        hook.on_bookmark("TASK123", "Progress note here")

        call_args = hook._http.post.call_args
        assert "TASK123" in call_args[0][0]
        assert call_args[1]["json"]["text"] == "Progress note here"


class TestOnComplete:
    def test_updates_status(self, monkeypatch):
        monkeypatch.setenv("WRDOCKET_ACCESS_TOKEN", "test-token")
        hook = WrikeHook("test-token")

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": [{"id": "TASK123", "status": "Completed"}]}
        mock_resp.raise_for_status = MagicMock()
        hook._http = MagicMock()
        hook._http.put.return_value = mock_resp

        hook.on_complete("TASK123")

        call_args = hook._http.put.call_args
        assert "TASK123" in call_args[0][0]
        assert call_args[1]["json"]["status"] == "Completed"
