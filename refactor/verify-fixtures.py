"""Replay golden fixtures against the Python ike_md and verify behavioral parity.

Strategy: Run fixtures in the same order as capture (sequential, stateful).
Each tool group gets the state it expects because we execute in capture order.
"""

import json
import os
import re
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ike_md.config import init_project, register_project, _guid_to_path
from ike_md.server import (
    project_init, project_set, project_list, project_info,
    task_create, task_list, task_view, task_edit, task_complete,
    task_search, task_archive,
    milestone_create, milestone_list, milestone_view, milestone_close,
    document_create, document_list, document_view, document_update,
)

FIXTURES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")

FN_MAP = {
    "project_init": project_init,
    "project_set": project_set,
    "project_list": project_list,
    "project_info": project_info,
    "task_create": task_create,
    "task_list": task_list,
    "task_view": task_view,
    "task_edit": task_edit,
    "task_complete": task_complete,
    "task_search": task_search,
    "task_archive": task_archive,
    "milestone_create": milestone_create,
    "milestone_list": milestone_list,
    "milestone_view": milestone_view,
    "milestone_close": milestone_close,
    "document_create": document_create,
    "document_list": document_list,
    "document_view": document_view,
    "document_update": document_update,
}


def normalize(text: str) -> str:
    """Normalize for comparison: replace paths, GUIDs, dates."""
    text = re.sub(r"/var/folders/[^\s]+", "<TMPDIR>", text)
    text = re.sub(r"/tmp/[^\s]+", "<TMPDIR>", text)
    text = re.sub(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", "<GUID>", text)
    # Normalize temp dir basenames used as default project names
    text = re.sub(r"\*\*ike-[a-z]+-[A-Za-z0-9_]+\*\*", "**<TMPNAME>**", text)
    text = re.sub(r"\*\*rmd-[a-z]+-[A-Za-z0-9_]+\*\*", "**<TMPNAME>**", text)
    return text


def run_fixture(tool_name: str, fixture: dict, project_id: str | None, tmp_dir: str) -> tuple[str, str]:
    """Run a fixture and return (actual_normalized, expected_normalized)."""
    args = {**fixture["input"]}
    fixture_id = fixture["fixture_id"]

    # Replace project_id with our current one
    if "project_id" in args and fixture_id != "005-bad-project-id":
        if project_id:
            args["project_id"] = project_id

    # For project_init/set, use tmp_dir
    if "path" in args and tool_name in ("project_init", "project_set"):
        if fixture_id == "002-no-project":
            args["path"] = "/nonexistent/path"
        else:
            args["path"] = tmp_dir

    fn = FN_MAP.get(tool_name)
    if not fn:
        return normalize(f"Unknown tool: {tool_name}"), ""

    try:
        actual = fn(**args)
    except (ValueError, Exception) as e:
        actual = f"Error: {e}"

    expected = fixture["output"]["content"][0]["text"] if fixture["output"].get("content") else ""

    return normalize(actual), normalize(expected)


def main():
    passed = 0
    failed = 0
    errors = []

    # ── Phase 1: project_init fixtures (each gets a fresh dir) ────────────
    for fixture_id in ["001-happy-path", "002-default-name", "003-idempotent"]:
        fp = os.path.join(FIXTURES_DIR, "project_init", f"{fixture_id}.json")
        if not os.path.exists(fp):
            continue
        with open(fp) as f:
            fixture = json.load(f)

        fresh = tempfile.mkdtemp(prefix="ike-v-")
        _guid_to_path.clear()

        if fixture_id == "003-idempotent":
            init_project(fresh, "first")
            register_project(fresh)

        args = {**fixture["input"]}
        args["path"] = fresh

        try:
            actual = project_init(**args)
        except Exception as e:
            actual = f"Error: {e}"

        expected = fixture["output"]["content"][0]["text"]
        a, e = normalize(actual), normalize(expected)

        if a == e:
            passed += 1
            print(f"  ✓ project_init/{fixture_id}")
        else:
            failed += 1
            errors.append(f"project_init/{fixture_id}")
            print(f"  ✗ project_init/{fixture_id}")
            print(f"    exp: {e[:150]}")
            print(f"    act: {a[:150]}")

    # ── Phase 2: project_set fixtures ─────────────────────────────────────
    for fixture_id in ["001-happy-path", "002-no-project"]:
        fp = os.path.join(FIXTURES_DIR, "project_set", f"{fixture_id}.json")
        if not os.path.exists(fp):
            continue
        with open(fp) as f:
            fixture = json.load(f)

        if fixture_id == "001-happy-path":
            fresh = tempfile.mkdtemp(prefix="ike-v-")
            _guid_to_path.clear()
            init_project(fresh, "set-test")
            try:
                actual = project_set(path=fresh)
            except Exception as e:
                actual = f"Error: {e}"
        elif fixture_id == "002-no-project":
            try:
                actual = project_set(path="/nonexistent/path")
            except Exception as e:
                actual = f"Error: {e}"

        expected = fixture["output"]["content"][0]["text"]
        a, e = normalize(actual), normalize(expected)

        if a == e:
            passed += 1
            print(f"  ✓ project_set/{fixture_id}")
        else:
            failed += 1
            errors.append(f"project_set/{fixture_id}")
            print(f"  ✗ project_set/{fixture_id}")
            print(f"    exp: {e[:150]}")
            print(f"    act: {a[:150]}")

    # ── Phase 3: Stateful task/milestone/document tests ───────────────────
    # Fresh project for all remaining tools
    _guid_to_path.clear()
    task_dir = tempfile.mkdtemp(prefix="ike-v-tasks-")
    config = init_project(task_dir, "task-tests")
    register_project(task_dir)
    pid = list(_guid_to_path.keys())[0]

    # Skip project_list (depends on exact number of registered projects from capture)
    print(f"  ~ project_list/001-with-projects (SKIP — stateful, depends on capture context)")

    # Run remaining fixtures in capture order
    ordered_tools = [
        ("task_create", ["001-minimal", "002-maximal", "003-draft-status", "004-unicode-title", "005-bad-project-id"]),
        ("task_list", ["001-all-tasks", "002-filter-status", "003-filter-tag", "004-filter-assignee"]),
        ("task_view", ["001-exists", "002-not-found"]),
        ("task_edit", ["001-update-fields", "002-append-notes", "003-set-blocked", "004-clear-blocked"]),
        ("task_complete", ["001-with-notes"]),
        ("task_search", ["001-match", "002-no-match"]),
        ("milestone_create", ["001-with-due", "002-minimal"]),
        ("milestone_list", ["001-with-milestones"]),
        ("milestone_view", ["001-exists"]),
        ("milestone_close", ["001-with-notes"]),
        ("project_info", ["001-with-data"]),
        ("document_create", ["001-with-content", "002-minimal"]),
        ("document_list", ["001-with-docs"]),
        ("document_view", ["001-exists", "002-not-found"]),
        ("document_update", ["001-replace-content", "002-append-content"]),
    ]

    for tool_name, fixture_ids in ordered_tools:
        for fixture_id in fixture_ids:
            fp = os.path.join(FIXTURES_DIR, tool_name, f"{fixture_id}.json")
            if not os.path.exists(fp):
                continue
            with open(fp) as f:
                fixture = json.load(f)

            args = {**fixture["input"]}

            # Handle project_id
            if "project_id" in args:
                if fixture_id == "005-bad-project-id":
                    args["project_id"] = "nonexistent-guid"
                else:
                    args["project_id"] = pid

            fn = FN_MAP[tool_name]
            try:
                actual = fn(**args)
            except (ValueError, Exception) as e:
                actual = f"Error: {e}"

            expected = fixture["output"]["content"][0]["text"]
            a, e = normalize(actual), normalize(expected)

            if a == e:
                passed += 1
                print(f"  ✓ {tool_name}/{fixture_id}")
            else:
                failed += 1
                errors.append(f"{tool_name}/{fixture_id}")
                print(f"  ✗ {tool_name}/{fixture_id}")
                print(f"    exp: {e[:200]}")
                print(f"    act: {a[:200]}")

    total = passed + failed + 1  # +1 for skipped project_list
    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed, 1 skipped out of {total}")
    print(f"Pass rate: {passed / (passed + failed) * 100:.1f}%" if (passed + failed) else "No fixtures")

    if errors:
        print(f"\nFailed:")
        for e in errors:
            print(f"  {e}")

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
