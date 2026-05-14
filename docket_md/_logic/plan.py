"""Plan CRUD: create, list, view, update, verify."""

from __future__ import annotations

from ..config import resolve_project
from ..files import (
    find_plan_file,
    list_plans,
    next_plan_id,
    plan_path,
    read_markdown,
    write_markdown,
)
from ._common import format_plan, today


def plan_create(
    project_id: str,
    title: str,
    content: str = "",
    tags: list[str] | None = None,
    verification: list[str] | None = None,
    milestone: str | None = None,
    session_id: str | None = None,
) -> str:
    """Create a new plan."""
    project_root = resolve_project(project_id)
    id = next_plan_id(project_root)
    fm: dict = {
        "id": id,
        "title": title,
        "status": "draft",
        "created": today(),
    }
    if session_id:
        fm["session_id"] = session_id
    if milestone:
        fm["milestone"] = milestone
    if tags:
        fm["tags"] = tags
    if verification:
        fm["verification"] = verification

    fp = plan_path(project_root, id, title)
    write_markdown(fp, fm, content)
    return f"Created plan **{id}** — {title}\nStatus: draft\nFile: {fp}"


def plan_list(project_id: str, status: str | None = None) -> str:
    """List plans."""
    project_root = resolve_project(project_id)
    plans = list_plans(project_root)
    if status:
        plans = [p for p in plans if p.frontmatter["status"] == status]
    if not plans:
        return "No plans found."
    lines = []
    for p in plans:
        fm = p.frontmatter
        badge = {
            "draft": "○",
            "approved": "✓",
            "in-progress": "▶",
            "completed": "✓",
            "abandoned": "✗",
        }.get(fm["status"], "?")
        ms = f" [{fm['milestone']}]" if fm.get("milestone") else ""
        lines.append(f"{badge} **{fm['id']}** — {fm['title']}{ms} ({fm['status']})")
    return "\n".join(lines)


def plan_view(project_id: str, plan_id: str) -> str:
    """View a plan in full detail."""
    project_root = resolve_project(project_id)
    fp = find_plan_file(project_root, plan_id)
    if not fp:
        return f"Plan {plan_id} not found."
    plan = read_markdown(fp)
    return format_plan(plan.frontmatter, plan.content)


def plan_update(
    project_id: str,
    plan_id: str,
    status: str | None = None,
    title: str | None = None,
    content: str | None = None,
    tags: list[str] | None = None,
    verification: list[str] | None = None,
    milestone: str | None = None,
    append_content: str | None = None,
) -> str:
    """Update a plan."""
    project_root = resolve_project(project_id)
    fp = find_plan_file(project_root, plan_id)
    if not fp:
        return f"Plan {plan_id} not found."
    plan = read_markdown(fp)
    fm = {**plan.frontmatter, "updated": today()}
    if title is not None:
        fm["title"] = title
    if status is not None:
        fm["status"] = status
        if status == "approved" and not plan.frontmatter.get("approved"):
            fm["approved"] = today()
    if tags is not None:
        fm["tags"] = tags
    if verification is not None:
        fm["verification"] = verification
    if milestone is not None:
        fm["milestone"] = milestone

    if append_content:
        new_content = f"{plan.content}\n\n{append_content}".strip()
    elif content is not None:
        new_content = content
    else:
        new_content = plan.content

    write_markdown(fp, fm, new_content)
    return f"Updated **{fm['id']}** — {fm['title']}"


def plan_verify(project_id: str, plan_id: str) -> str:
    """Return a plan's verification criteria as a checklist."""
    project_root = resolve_project(project_id)
    fp = find_plan_file(project_root, plan_id)
    if not fp:
        return f"Plan {plan_id} not found."
    plan = read_markdown(fp)
    fm = plan.frontmatter
    verification = fm.get("verification", [])
    if not verification:
        return f"Plan **{fm['id']}** has no verification criteria defined."
    lines = [f"## Verification — {fm['id']} — {fm['title']}\n"]
    for i, v in enumerate(verification, 1):
        lines.append(f"- [ ] {i}. {v}")
    return "\n".join(lines)
