"""Tests for hierarchical config resolution."""

import json
import os
import pytest
from unittest.mock import patch

from ike_md.hier_config import (
    deep_merge,
    parse_git_remote,
    read_settings,
    write_settings,
    resolve_config_chain,
    resolved_settings,
    set_value,
    find_setting_origin,
    get_config_tree,
    IKE_CONFIG_ROOT,
)


# ---------------------------------------------------------------------------
# deep_merge
# ---------------------------------------------------------------------------

class TestDeepMerge:
    def test_simple_override(self):
        assert deep_merge({"a": 1}, {"a": 2}) == {"a": 2}

    def test_additive(self):
        assert deep_merge({"a": 1}, {"b": 2}) == {"a": 1, "b": 2}

    def test_nested_merge(self):
        base = {"wrike": {"enabled": True, "folder_id": "ABC"}}
        override = {"wrike": {"folder_id": "XYZ"}}
        result = deep_merge(base, override)
        assert result == {"wrike": {"enabled": True, "folder_id": "XYZ"}}

    def test_child_replaces_scalar_with_dict(self):
        assert deep_merge({"a": 1}, {"a": {"nested": True}}) == {"a": {"nested": True}}

    def test_empty_override(self):
        assert deep_merge({"a": 1}, {}) == {"a": 1}

    def test_empty_base(self):
        assert deep_merge({}, {"a": 1}) == {"a": 1}

    def test_three_levels(self):
        a = {"x": {"y": 1, "z": 2}}
        b = {"x": {"z": 3, "w": 4}}
        c = {"x": {"w": 5}}
        result = deep_merge(deep_merge(a, b), c)
        assert result == {"x": {"y": 1, "z": 3, "w": 5}}


# ---------------------------------------------------------------------------
# parse_git_remote
# ---------------------------------------------------------------------------

class TestParseGitRemote:
    def test_ssh(self):
        assert parse_git_remote("git@github.com:aic-holdings/ciso.git") == ("aic-holdings", "ciso")

    def test_https_with_git(self):
        assert parse_git_remote("https://github.com/aic-holdings/ciso.git") == ("aic-holdings", "ciso")

    def test_https_without_git(self):
        assert parse_git_remote("https://github.com/aic-holdings/ciso") == ("aic-holdings", "ciso")

    def test_invalid(self):
        assert parse_git_remote("not-a-url") is None

    def test_gitlab_ssh(self):
        assert parse_git_remote("git@gitlab.com:myorg/myrepo.git") == ("myorg", "myrepo")


# ---------------------------------------------------------------------------
# Settings I/O
# ---------------------------------------------------------------------------

class TestSettingsIO:
    def test_read_missing(self, tmp_path):
        assert read_settings(str(tmp_path / "nope.json")) == {}

    def test_roundtrip(self, tmp_path):
        sp = str(tmp_path / "settings.json")
        data = {"wrike": {"enabled": True}}
        write_settings(sp, data)
        assert read_settings(sp) == data

    def test_read_malformed(self, tmp_path):
        sp = tmp_path / "settings.json"
        sp.write_text("not json{{{")
        assert read_settings(str(sp)) == {}


# ---------------------------------------------------------------------------
# Config chain resolution
# ---------------------------------------------------------------------------

class TestResolveConfigChain:
    def test_full_chain(self, tmp_path, monkeypatch):
        config_root = str(tmp_path / "config" / "ike")
        monkeypatch.setattr("ike_md.hier_config.IKE_CONFIG_ROOT", config_root)

        # Create settings at each level
        global_s = {"theme": "dark"}
        org_s = {"wrike": {"enabled": True, "folder_id": "ORG"}}
        repo_s = {"wrike": {"folder_id": "REPO"}}
        proj_s = {"custom": "value"}

        os.makedirs(config_root, exist_ok=True)
        write_settings(os.path.join(config_root, "settings.json"), global_s)

        org_dir = os.path.join(config_root, "orgs", "testorg")
        write_settings(os.path.join(org_dir, "settings.json"), org_s)

        repo_dir = os.path.join(org_dir, "repos", "testrepo")
        write_settings(os.path.join(repo_dir, "settings.json"), repo_s)

        proj_dir = os.path.join(repo_dir, "projects", "uuid-123")
        write_settings(os.path.join(proj_dir, "settings.json"), proj_s)

        with patch("ike_md.hier_config.detect_org_repo", return_value=("testorg", "testrepo")):
            chain = resolve_config_chain("/fake/path", project_id="uuid-123")

        assert len(chain) == 4
        assert chain[0][0] == "global"
        assert chain[1][0] == "org"
        assert chain[2][0] == "repo"
        assert chain[3][0] == "project"

        # Verify merged settings
        with patch("ike_md.hier_config.detect_org_repo", return_value=("testorg", "testrepo")):
            merged = resolved_settings("/fake/path", project_id="uuid-123")

        assert merged["theme"] == "dark"
        assert merged["wrike"]["enabled"] is True
        assert merged["wrike"]["folder_id"] == "REPO"  # repo overrides org
        assert merged["custom"] == "value"

    def test_missing_levels(self, tmp_path, monkeypatch):
        config_root = str(tmp_path / "config" / "ike")
        monkeypatch.setattr("ike_md.hier_config.IKE_CONFIG_ROOT", config_root)

        # Only global exists
        os.makedirs(config_root, exist_ok=True)
        write_settings(os.path.join(config_root, "settings.json"), {"theme": "light"})

        with patch("ike_md.hier_config.detect_org_repo", return_value=("myorg", "myrepo")):
            merged = resolved_settings("/fake/path", project_id="uuid-456")

        assert merged == {"theme": "light"}

    def test_no_git_remote(self, tmp_path, monkeypatch):
        config_root = str(tmp_path / "config" / "ike")
        monkeypatch.setattr("ike_md.hier_config.IKE_CONFIG_ROOT", config_root)

        os.makedirs(config_root, exist_ok=True)
        write_settings(os.path.join(config_root, "settings.json"), {"a": 1})

        with patch("ike_md.hier_config.detect_org_repo", return_value=(None, None)):
            chain = resolve_config_chain("/fake/path", project_id="uuid-789")

        # Only global level
        assert len(chain) == 1
        assert chain[0][0] == "global"


# ---------------------------------------------------------------------------
# set_value
# ---------------------------------------------------------------------------

class TestSetValue:
    def test_set_dotted_key(self, tmp_path, monkeypatch):
        config_root = str(tmp_path / "config" / "ike")
        monkeypatch.setattr("ike_md.hier_config.IKE_CONFIG_ROOT", config_root)

        with patch("ike_md.hier_config.detect_org_repo", return_value=("org1", "repo1")):
            sp = set_value("/fake", "wrike.enabled", True, level="org")

        data = read_settings(sp)
        assert data["wrike"]["enabled"] is True

    def test_set_global(self, tmp_path, monkeypatch):
        config_root = str(tmp_path / "config" / "ike")
        monkeypatch.setattr("ike_md.hier_config.IKE_CONFIG_ROOT", config_root)

        sp = set_value("/fake", "theme", "dark", level="global")
        data = read_settings(sp)
        assert data["theme"] == "dark"


# ---------------------------------------------------------------------------
# find_setting_origin
# ---------------------------------------------------------------------------

class TestFindSettingOrigin:
    def test_finds_deepest_level(self, tmp_path, monkeypatch):
        config_root = str(tmp_path / "config" / "ike")
        monkeypatch.setattr("ike_md.hier_config.IKE_CONFIG_ROOT", config_root)

        os.makedirs(config_root, exist_ok=True)
        write_settings(os.path.join(config_root, "settings.json"), {"wrike": {"enabled": True}})

        org_dir = os.path.join(config_root, "orgs", "org1")
        write_settings(os.path.join(org_dir, "settings.json"), {"wrike": {"enabled": False}})

        with patch("ike_md.hier_config.detect_org_repo", return_value=("org1", "repo1")):
            result = find_setting_origin("wrike.enabled", "/fake", project_id="uuid-1")

        assert result == ("org", False)

    def test_not_found(self, tmp_path, monkeypatch):
        config_root = str(tmp_path / "config" / "ike")
        monkeypatch.setattr("ike_md.hier_config.IKE_CONFIG_ROOT", config_root)
        os.makedirs(config_root, exist_ok=True)

        with patch("ike_md.hier_config.detect_org_repo", return_value=(None, None)):
            result = find_setting_origin("nonexistent.key", "/fake")

        assert result is None


# ---------------------------------------------------------------------------
# get_config_tree
# ---------------------------------------------------------------------------

class TestGetConfigTree:
    def test_empty(self, tmp_path, monkeypatch):
        monkeypatch.setattr("ike_md.hier_config.IKE_CONFIG_ROOT", str(tmp_path / "empty"))
        assert get_config_tree() == {}

    def test_populated(self, tmp_path, monkeypatch):
        config_root = str(tmp_path / "config" / "ike")
        monkeypatch.setattr("ike_md.hier_config.IKE_CONFIG_ROOT", config_root)

        write_settings(os.path.join(config_root, "settings.json"), {"g": 1})
        org_dir = os.path.join(config_root, "orgs", "org1")
        write_settings(os.path.join(org_dir, "settings.json"), {"o": 2})
        repo_dir = os.path.join(org_dir, "repos", "repo1")
        write_settings(os.path.join(repo_dir, "settings.json"), {"r": 3})

        tree = get_config_tree()
        assert tree["global"] == {"g": 1}
        assert tree["orgs"]["org1"]["_settings"] == {"o": 2}
        assert tree["orgs"]["org1"]["repos"]["repo1"]["_settings"] == {"r": 3}
