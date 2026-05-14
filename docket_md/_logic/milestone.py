"""Milestone CRUD: create, list, view, close."""

from __future__ import annotations

from ..config import resolve_project
from ..files import (
    find_milestone_file,
    list_milestones,
    milestone_path,
    next_milestone_id,
    read_markdown,
    write_markdown,
)
from ._common import today


def milestone_create(
    project_id: str, title: str, description: str = "", due: str | None = None
) -> str:
    """Create a new milestone."""
    project_root = resolve_project(project_id)
    id = next_milestone_id(project_root)
    fm: dict = {"id": id, "title": title, "status": "open", "created": today()}
    if due:
        fm["due"] = due
    write_markdown(milestone_path(project_root, id, title), fm, description)
    return f"Created milestone **{id}** — {title}"


def milestone_list(project_id: str) -> str:
    """List all milestones."""
    project_root = resolve_project(project_id)
    milestones = list_milestones(project_root)
    if not milestones:
        return "No milestones."
    lines = []
    for m in milestones:
        fm = m.frontmatter
        due = f" (due {fm['due']})" if fm.get("due") else ""
        badge = "○" if fm["status"] == "open" else "✓"
        lines.append(f"{badge} **{fm['id']}** — {fm['title']}{due}")
    return "\n".join(lines)


def milestone_view(project_id: str, milestone_id: str) -> str:
    """View a milestone in full detail."""
    project_root = resolve_project(project_id)
    fp = find_milestone_file(project_root, milestone_id)
    if not fp:
        return f"Milestone {milestone_id} not found."
    m = read_markdown(fp)
    fm = m.frontmatter
    lines = [
        f"## {fm['id']} — {fm['title']}",
        f"**Status:** {fm['status']}",
    ]
    if fm.get("due"):
        lines.append(f"**Due:** {fm['due']}")
    lines.append(f"**Created:** {fm['created']}")
    if m.content:
        lines.append("")
        lines.append(m.content)
    return "\n".join(lines)


def milestone_close(
    project_id: str, milestone_id: str, notes: str | None = None
) -> str:
    """Close a milestone."""
    project_root = resolve_project(project_id)
    fp = find_milestone_file(project_root, milestone_id)
    if not fp:
        return f"Milestone {milestone_id} not found."
    m = read_markdown(fp)
    fm = {**m.frontmatter, "status": "closed"}
    content = f"{m.content}\n\n**Closed:** {notes}".strip() if notes else m.content
    write_markdown(fp, fm, content)
    return f"Closed milestone **{fm['id']}** — {fm['title']}"
