"""Task CRUD + complete/archive/search."""

from __future__ import annotations

import os

from ..config import DIRECTORIES, DOCKET_DIR, resolve_project
from ..files import (
    find_task_file,
    list_all_tasks,
    list_tasks,
    next_task_id,
    read_markdown,
    task_path,
    write_markdown,
)
from ..security import safe_path
from ._common import format_task, today


def task_create(
    project_id: str,
    title: str,
    description: str = "",
    status: str = "To Do",
    priority: str | None = None,
    milestone: str | None = None,
    assignees: list[str] | None = None,
    tags: list[str] | None = None,
    dependencies: list[str] | None = None,
    acceptance_criteria: list[str] | None = None,
    definition_of_done: list[str] | None = None,
    visionlog_goal_id: str | None = None,
    blocked_reason: str | None = None,
) -> str:
    """Create a new task."""
    project_root = resolve_project(project_id)
    id = next_task_id(project_root)
    fm: dict = {
        "id": id,
        "title": title,
        "status": status,
        "created": today(),
    }
    if priority:
        fm["priority"] = priority
    if milestone:
        fm["milestone"] = milestone
    if assignees:
        fm["assignees"] = assignees
    if tags:
        fm["tags"] = tags
    if dependencies:
        fm["dependencies"] = dependencies
    if acceptance_criteria:
        fm["acceptance-criteria"] = acceptance_criteria
    if definition_of_done:
        fm["definition-of-done"] = definition_of_done
    if visionlog_goal_id:
        fm["visionlog_goal_id"] = visionlog_goal_id
    if blocked_reason:
        fm["blocked_reason"] = blocked_reason

    fp = task_path(project_root, id, title)
    write_markdown(fp, fm, description)
    return f"Created **{id}** — {title}\nStatus: {status}\nFile: {fp}"


def task_list(
    project_id: str,
    status: str | None = None,
    milestone: str | None = None,
    assignee: str | None = None,
    tag: str | None = None,
    include_completed: bool = False,
) -> str:
    """List tasks with optional filtering."""
    project_root = resolve_project(project_id)
    tasks = list_tasks(project_root, include_completed)
    if status:
        tasks = [t for t in tasks if t.frontmatter["status"] == status]
    if milestone:
        tasks = [t for t in tasks if t.frontmatter.get("milestone") == milestone]
    if assignee:
        tasks = [t for t in tasks if assignee in (t.frontmatter.get("assignees") or [])]
    if tag:
        tasks = [t for t in tasks if tag in (t.frontmatter.get("tags") or [])]
    if not tasks:
        return "No tasks found."
    lines = []
    for t in tasks:
        fm = t.frontmatter
        if fm.get("blocked_reason"):
            badge = "⛔"
        elif fm["status"] == "Done":
            badge = "✓"
        elif fm["status"] == "In Progress":
            badge = "▶"
        else:
            badge = "○"
        pri = f" [{fm['priority']}]" if fm.get("priority") else ""
        blocked = (
            f" — BLOCKED: {fm['blocked_reason']}" if fm.get("blocked_reason") else ""
        )
        lines.append(f"{badge} **{fm['id']}**{pri} — {fm['title']}{blocked}")
    return "\n".join(lines)


def task_view(project_id: str, task_id: str) -> str:
    """View a task in full detail by ID."""
    project_root = resolve_project(project_id)
    fp = find_task_file(project_root, task_id)
    if not fp:
        return f"Task {task_id} not found."
    task = read_markdown(fp)
    return format_task(task.frontmatter, task.content)


def task_edit(
    project_id: str,
    task_id: str,
    title: str | None = None,
    description: str | None = None,
    status: str | None = None,
    priority: str | None = None,
    milestone: str | None = None,
    assignees: list[str] | None = None,
    tags: list[str] | None = None,
    dependencies: list[str] | None = None,
    acceptance_criteria: list[str] | None = None,
    definition_of_done: list[str] | None = None,
    blocked_reason: str | None = None,
    append_notes: str | None = None,
) -> str:
    """Edit a task's fields."""
    project_root = resolve_project(project_id)
    fp = find_task_file(project_root, task_id)
    if not fp:
        return f"Task {task_id} not found."
    task = read_markdown(fp)
    fm = {**task.frontmatter, "updated": today()}
    if title is not None:
        fm["title"] = title
    if status is not None:
        fm["status"] = status
    if priority is not None:
        fm["priority"] = priority
    if milestone is not None:
        fm["milestone"] = milestone
    if assignees is not None:
        fm["assignees"] = assignees
    if tags is not None:
        fm["tags"] = tags
    if dependencies is not None:
        fm["dependencies"] = dependencies
    if acceptance_criteria is not None:
        fm["acceptance-criteria"] = acceptance_criteria
    if definition_of_done is not None:
        fm["definition-of-done"] = definition_of_done
    if blocked_reason is not None:
        if blocked_reason == "":
            fm.pop("blocked_reason", None)
        else:
            fm["blocked_reason"] = blocked_reason

    if append_notes:
        content = f"{task.content}\n\n{append_notes}".strip()
    elif description is not None:
        content = description
    else:
        content = task.content

    write_markdown(fp, fm, content)
    return f"Updated **{fm['id']}** — {fm['title']}"


def task_complete(project_id: str, task_id: str, notes: str | None = None) -> str:
    """Mark a task as Done and move it to completed/."""
    project_root = resolve_project(project_id)
    fp = find_task_file(project_root, task_id)
    if not fp:
        return f"Task {task_id} not found."
    task = read_markdown(fp)
    fm = {**task.frontmatter, "status": "Done", "updated": today()}
    content = (
        f"{task.content}\n\n**Completion notes:** {notes}".strip()
        if notes
        else task.content
    )
    dest = task_path(project_root, fm["id"], fm["title"], completed=True)
    write_markdown(dest, fm, content)
    os.unlink(fp)
    return f"Completed **{fm['id']}** — {fm['title']}\nMoved to completed/"


def task_archive(project_id: str, task_id: str, reason: str | None = None) -> str:
    """Archive a task."""
    project_root = resolve_project(project_id)
    fp = find_task_file(project_root, task_id)
    if not fp:
        return f"Task {task_id} not found."
    task = read_markdown(fp)
    fm = {**task.frontmatter, "updated": today()}
    content = (
        f"{task.content}\n\n**Archived:** {reason}".strip() if reason else task.content
    )
    archive_path = safe_path(
        project_root, DOCKET_DIR, DIRECTORIES["ARCHIVE"], os.path.basename(fp)
    )
    write_markdown(archive_path, fm, content)
    os.unlink(fp)
    return f"Archived **{fm['id']}** — {fm['title']}"


def task_search(project_id: str, query: str, include_completed: bool = False) -> str:
    """Search tasks by keyword."""
    project_root = resolve_project(project_id)
    tasks = (
        list_all_tasks(project_root)
        if include_completed
        else list_tasks(project_root, False)
    )
    q = query.lower()
    matches = [
        t
        for t in tasks
        if q in t.frontmatter["title"].lower() or q in t.content.lower()
    ]
    if not matches:
        return f'No tasks matching "{query}".'
    return "\n".join(
        f"**{t.frontmatter['id']}** — {t.frontmatter['title']} [{t.frontmatter['status']}]"
        for t in matches
    )
