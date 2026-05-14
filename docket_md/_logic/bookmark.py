"""Bookmark a project's current state."""

from __future__ import annotations

import os
from datetime import datetime

from ..config import DOCKET_DIR, load_config, resolve_project
from ..hier_config import resolved_settings


def bookmark(project_id: str, note: str) -> str:
    """Bookmark the current state of a project with a note.

    Saves a timestamped checkpoint locally. If Wrike sync is enabled,
    pushes the note as a comment on the linked Wrike task.
    """
    project_root = resolve_project(project_id)
    config = load_config(project_root)
    project_name = config.project if config else "unknown"

    docket_dir = os.path.join(project_root, DOCKET_DIR)
    bookmarks_file = os.path.join(docket_dir, "bookmarks.md")
    timestamp = datetime.now().isoformat()
    entry = f"\n## {timestamp}\n\n{note}\n"

    with open(bookmarks_file, "a") as f:
        f.write(entry)

    settings = resolved_settings(project_root, project_id=project_id)
    wrike_cfg = settings.get("wrike", {})
    wrike_result = ""

    if wrike_cfg.get("enabled") and wrike_cfg.get("task_id"):
        try:
            from ..hooks.wrike_hook import get_hook

            hook = get_hook(settings)
            if hook:
                hook.on_bookmark(
                    wrike_cfg["task_id"],
                    f"[ike checkpoint] {project_name}\n\n{note}",
                )
                wrike_result = "\nWrike comment posted."
        except Exception as e:
            wrike_result = f"\nWrike hook failed: {e}"

    return f"Bookmarked at {timestamp}{wrike_result}"
