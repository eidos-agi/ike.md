"""Project lifecycle: init, set, list, info."""

from __future__ import annotations

import os

from ..config import (
    init_project,
    list_registered,
    load_config,
    register_project,
    resolve_project,
)
from ..files import (
    list_all_tasks,
    list_documents,
    list_milestones,
    list_plans,
)


def project_init(path: str, name: str | None = None) -> str:
    """Initialize a new docket.md project."""
    config = init_project(path, name)
    try:
        register_project(os.path.abspath(path))
    except Exception:
        pass
    return (
        f"Project initialized: **{config.project}**\nproject_id: `{config.id}`\n"
        f"Path: {path}\n\nUse this project_id in all subsequent calls."
    )


def project_set(path: str) -> str:
    """Register an existing docket.md project for this session."""
    result = register_project(path)
    return (
        f"Project registered: **{result['project']}**\nproject_id: `{result['id']}`\n\n"
        "Use this project_id in all subsequent calls."
    )


def project_list() -> str:
    """List all projects registered in this session."""
    projects = list_registered()
    if not projects:
        return (
            "No projects registered this session. Call project_set with a project path."
        )
    return "\n".join(f"- `{p['id']}` → {p['path']}" for p in projects)


def project_info(project_id: str) -> str:
    """Show project stats."""
    project_root = resolve_project(project_id)
    config = load_config(project_root)
    name = config.project if config else os.path.basename(project_root)
    all_tasks = list_all_tasks(project_root)
    counts: dict[str, int] = {}
    for t in all_tasks:
        s = t.frontmatter["status"]
        counts[s] = counts.get(s, 0) + 1
    milestones = list_milestones(project_root)
    open_ms = sum(1 for m in milestones if m.frontmatter["status"] == "open")
    docs = list_documents(project_root)
    plans = list_plans(project_root)
    status_line = " · ".join(f"{s}: {n}" for s, n in counts.items()) or "none"
    lines = [
        f"## {name}",
        f"project_id: `{project_id}`",
        f"Path: {project_root}",
        "",
        f"**Tasks:** {status_line}",
        f"**Milestones:** {open_ms} open, {len(milestones) - open_ms} closed",
        f"**Documents:** {len(docs)}",
        f"**Plans:** {len(plans)}",
    ]
    return "\n".join(lines)
