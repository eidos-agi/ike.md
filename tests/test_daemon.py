"""Tests for ike_md.daemon — plan approval detection, ingestion, install, queue, and watching."""

import json
import os
import tempfile

import pytest

from ike_md.daemon import (
    _extract_title,
    _ingest_plan,
    _is_plan_approval,
    install,
    process_queue,
    watch_files,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

def _make_approval_entry(plan: str = "# My Plan\n\nDo the thing.", session_id: str = "abc-123"):
    """Build a realistic plan-approval JSONL dict."""
    return {
        "type": "user",
        "message": {
            "content": [
                {
                    "type": "tool_result",
                    "content": "User has approved your plan and it will be saved.",
                }
            ]
        },
        "toolUseResult": {
            "plan": plan,
            "filePath": "/tmp/.claude/plans/my-plan.md",
        },
        "sessionId": session_id,
    }


def _make_ike_project(tmpdir: str, project_name: str = "test-project") -> str:
    """Set up a minimal .ike project in tmpdir, return project root."""
    ike_dir = os.path.join(tmpdir, ".ike")
    os.makedirs(os.path.join(ike_dir, "plans"), exist_ok=True)
    with open(os.path.join(ike_dir, "ike.json"), "w") as f:
        json.dump({
            "id": "test-guid-1234",
            "version": "0.1.0",
            "project": project_name,
            "created": "2026-01-01",
            "ike_path": ".ike",
        }, f)
    return tmpdir


# ── Detection tests ──────────────────────────────────────────────────────────

def test_is_plan_approval_match():
    entry = _make_approval_entry()
    result = _is_plan_approval(entry)
    assert result is not None
    assert result["plan_content"] == "# My Plan\n\nDo the thing."
    assert result["plan_path"] == "/tmp/.claude/plans/my-plan.md"
    assert result["session_id"] == "abc-123"


def test_is_plan_approval_no_match_assistant():
    entry = {"type": "assistant", "message": {"content": "Hello!"}}
    assert _is_plan_approval(entry) is None


def test_is_plan_approval_no_match_missing_tool_result():
    entry = {
        "type": "user",
        "message": {"content": [{"type": "text", "text": "just chatting"}]},
    }
    assert _is_plan_approval(entry) is None


def test_is_plan_approval_no_match_no_approved_text():
    entry = {
        "type": "user",
        "message": {
            "content": [
                {"type": "tool_result", "content": "Some other tool result"}
            ]
        },
        "toolUseResult": {
            "plan": "# A Plan",
            "filePath": "/tmp/plan.md",
        },
        "sessionId": "xyz",
    }
    assert _is_plan_approval(entry) is None


# ── Title extraction tests ───────────────────────────────────────────────────

def test_extract_title_heading():
    assert _extract_title("# Deploy the Widget\n\nSteps here.") == "Deploy the Widget"


def test_extract_title_no_heading():
    assert _extract_title("Just some text without a heading") == "Untitled Plan"


def test_extract_title_later_heading():
    md = "Some preamble\n\n# Actual Title\n\nBody."
    assert _extract_title(md) == "Actual Title"


# ── Ingestion tests ──────────────────────────────────────────────────────────

def test_ingest_plan():
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = _make_ike_project(tmpdir)
        approval = {
            "plan_content": "# Widget Deploy\n\nStep 1: do it.",
            "plan_path": "/tmp/plan.md",
            "session_id": "sess-001",
        }
        plan_id = _ingest_plan(project_root, approval)
        assert plan_id is not None
        assert plan_id.startswith("PLAN-")

        plans_dir = os.path.join(project_root, ".ike", "plans")
        files = os.listdir(plans_dir)
        assert len(files) == 1
        assert files[0].startswith("PLAN-")
        assert files[0].endswith(".md")


def test_deduplication():
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = _make_ike_project(tmpdir)
        approval = {
            "plan_content": "# Same Plan Title\n\nContent here.",
            "plan_path": "/tmp/plan.md",
            "session_id": "sess-002",
        }
        first = _ingest_plan(project_root, approval)
        assert first is not None

        second = _ingest_plan(project_root, approval)
        assert second is None

        plans_dir = os.path.join(project_root, ".ike", "plans")
        files = [f for f in os.listdir(plans_dir) if f.endswith(".md")]
        assert len(files) == 1


# ── Install tests ────────────────────────────────────────────────────────────

def test_install_creates_hook(tmp_path, monkeypatch):
    """install() creates settings.json with the SessionStart hook."""
    settings_file = str(tmp_path / "settings.json")
    monkeypatch.setattr("ike_md.daemon.SETTINGS_FILE", settings_file)

    install()

    with open(settings_file) as f:
        settings = json.load(f)

    hooks = settings["hooks"]["SessionStart"]
    assert len(hooks) == 1
    assert "daemon-queue.jsonl" in hooks[0]["hooks"][0]["command"]


def test_install_merges_existing(tmp_path, monkeypatch):
    """install() preserves existing hooks and doesn't duplicate."""
    settings_file = str(tmp_path / "settings.json")
    monkeypatch.setattr("ike_md.daemon.SETTINGS_FILE", settings_file)

    # Pre-existing settings with another hook
    existing = {
        "hooks": {
            "SessionStart": [
                {
                    "matcher": "",
                    "hooks": [{"type": "command", "command": "echo hello", "timeout": 5}],
                }
            ],
            "PostToolUse": [
                {
                    "matcher": "",
                    "hooks": [{"type": "command", "command": "echo post", "timeout": 5}],
                }
            ],
        }
    }
    with open(settings_file, "w") as f:
        json.dump(existing, f)

    install()

    with open(settings_file) as f:
        settings = json.load(f)

    # Original SessionStart hook preserved, ike hook added
    session_hooks = settings["hooks"]["SessionStart"]
    assert len(session_hooks) == 2
    assert settings["hooks"]["PostToolUse"]  # preserved

    # Install again — should not duplicate
    install()
    with open(settings_file) as f:
        settings = json.load(f)
    assert len(settings["hooks"]["SessionStart"]) == 2


# ── Queue processing tests ───────────────────────────────────────────────────

def test_process_queue(tmp_path, monkeypatch):
    """process_queue() picks up watch_session jobs and adds watches."""
    queue_file = str(tmp_path / "daemon-queue.jsonl")
    monkeypatch.setattr("ike_md.daemon.QUEUE_FILE", queue_file)

    project_root = _make_ike_project(str(tmp_path / "myproject"))

    # Create a fake JSONL transcript file
    jsonl_path = str(tmp_path / "session.jsonl")
    with open(jsonl_path, "w") as f:
        f.write('{"type":"assistant","message":{"content":"hi"}}\n')

    # Write a queue job
    job = {
        "type": "watch_session",
        "session_id": "sess-abc",
        "jsonl": jsonl_path,
        "cwd": project_root,
    }
    with open(queue_file, "w") as f:
        f.write(json.dumps(job) + "\n")

    state = {"watches": {}, "ingested": []}
    state = process_queue(state)

    # Session should be in watches
    assert jsonl_path in state["watches"]
    watch = state["watches"][jsonl_path]
    assert watch["session_id"] == "sess-abc"
    assert watch["project_root"] == project_root
    assert watch["project_id"] == "test-guid-1234"
    # Offset should be at current file size (watermark)
    assert watch["offset"] == os.path.getsize(jsonl_path)

    # Queue file should be truncated
    with open(queue_file) as f:
        assert f.read().strip() == ""


def test_process_queue_skips_non_ike(tmp_path, monkeypatch):
    """process_queue() skips projects without .ike/ike.json."""
    queue_file = str(tmp_path / "daemon-queue.jsonl")
    monkeypatch.setattr("ike_md.daemon.QUEUE_FILE", queue_file)

    # Create a directory without .ike
    non_ike_dir = str(tmp_path / "plain-project")
    os.makedirs(non_ike_dir)

    jsonl_path = str(tmp_path / "session2.jsonl")
    with open(jsonl_path, "w") as f:
        f.write('{"type":"assistant"}\n')

    job = {
        "type": "watch_session",
        "session_id": "sess-xyz",
        "jsonl": jsonl_path,
        "cwd": non_ike_dir,
    }
    with open(queue_file, "w") as f:
        f.write(json.dumps(job) + "\n")

    state = {"watches": {}, "ingested": []}
    state = process_queue(state)

    # Should NOT be in watches
    assert jsonl_path not in state["watches"]
    assert len(state["watches"]) == 0


# ── Watch tests ──────────────────────────────────────────────────────────────

def test_watch_detects_approval(tmp_path, monkeypatch):
    """watch_files() detects a plan approval appended after the offset watermark."""
    project_root = _make_ike_project(str(tmp_path / "proj"))

    jsonl_path = str(tmp_path / "transcript.jsonl")

    # Write some initial content (before the watermark)
    initial_line = json.dumps({"type": "assistant", "message": {"content": "hi"}})
    with open(jsonl_path, "w") as f:
        f.write(initial_line + "\n")

    initial_size = os.path.getsize(jsonl_path)

    state = {
        "watches": {
            jsonl_path: {
                "project_root": project_root,
                "project_id": "test-guid-1234",
                "session_id": "sess-watch",
                "offset": initial_size,
            }
        },
        "ingested": [],
    }

    # Now append a plan approval AFTER the watermark
    approval_entry = _make_approval_entry(
        plan="# Watch Test Plan\n\nThis should be ingested.",
        session_id="sess-watch",
    )
    with open(jsonl_path, "a") as f:
        f.write(json.dumps(approval_entry) + "\n")

    # Monkeypatch add_session_event to avoid needing full sessions.json setup
    monkeypatch.setattr("ike_md.daemon.HAS_SESSION_HELPERS", False)

    state = watch_files(state)

    # Plan should have been ingested
    plans_dir = os.path.join(project_root, ".ike", "plans")
    plan_files = [f for f in os.listdir(plans_dir) if f.endswith(".md")]
    assert len(plan_files) == 1
    assert plan_files[0].startswith("PLAN-")

    # Dedup key should be recorded
    assert len(state["ingested"]) == 1
    assert "sess-watch:Watch Test Plan" in state["ingested"][0]

    # Offset should have advanced
    assert state["watches"][jsonl_path]["offset"] > initial_size
