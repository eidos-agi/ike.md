"""ike.md MCP server — all 21 tools."""

import os
from datetime import date
from mcp.server.fastmcp import FastMCP

from .config import (
    init_project,
    register_project,
    resolve_project,
    list_registered,
    load_config,
)
from .files import (
    list_tasks,
    list_all_tasks,
    next_task_id,
    task_path,
    find_task_file,
    read_markdown,
    write_markdown,
    list_milestones,
    next_milestone_id,
    milestone_path,
    find_milestone_file,
    list_documents,
    next_document_id,
    document_path,
    find_document_file,
)
from .security import safe_path
from .config import IKE_DIR, DIRECTORIES

INSTRUCTIONS = """ike.md is the execution forge — tasks, milestones, documents, Definition of Done. This is where work gets done.

Named for Eisenhower — the man who planned D-Day and then ran the free world. Ike didn't just plan. He executed at scale, across many agents, under time pressure, with contracts that had to be honored.

READ visionlog at the start of every session before touching anything. visionlog is the static St. Peter: it tells you where the ladder points, what the project has committed to, and what guardrails you must not cross. If a task would violate a visionlog guardrail, St. Peter has already told you no — adjust before you start.

Before making a consequential decision that spawns tasks, use research.md to earn that decision with evidence. Then record it in visionlog as an ADR. Then create tasks here to execute it.

The trilogy:
- research.md: decide with evidence
- visionlog: record vision, goals, guardrails, SOPs, ADRs — the contracts all execution must honor
- ike.md: execute within those contracts — this is where you are now

GUID workflow: Call project_set with the project path to register it and get its project_id. Pass that project_id to every subsequent tool call. For a new project, call project_init first."""

mcp = FastMCP("ike.md", instructions=INSTRUCTIONS)


def _today() -> str:
    return date.today().isoformat()


def _format_task(fm: dict, content: str) -> str:
    lines = [
        f"## {fm['id']} — {fm['title']}",
        f"**Status:** {fm['status']}",
    ]
    if fm.get("priority"):
        lines.append(f"**Priority:** {fm['priority']}")
    if fm.get("milestone"):
        lines.append(f"**Milestone:** {fm['milestone']}")
    if fm.get("assignees"):
        lines.append(f"**Assignees:** {', '.join(fm['assignees'])}")
    if fm.get("tags"):
        lines.append(f"**Tags:** {', '.join(fm['tags'])}")
    if fm.get("dependencies"):
        lines.append(f"**Depends on:** {', '.join(fm['dependencies'])}")
    if fm.get("blocked_reason"):
        lines.append(f"**⛔ Blocked:** {fm['blocked_reason']}")
    lines.append(f"**Created:** {fm['created']}")
    if fm.get("updated"):
        lines.append(f"**Updated:** {fm['updated']}")

    if fm.get("acceptance-criteria"):
        lines.append("\n**Acceptance Criteria:**")
        for c in fm["acceptance-criteria"]:
            lines.append(f"- [ ] {c}")

    if fm.get("definition-of-done"):
        lines.append("\n**Definition of Done:**")
        for d in fm["definition-of-done"]:
            lines.append(f"- [ ] {d}")

    if content:
        lines.append("\n**Notes:**")
        lines.append(content)

    return "\n".join(lines)


# ── Projects ──────────────────────────────────────────────────────────────────


@mcp.tool()
def project_init(path: str, name: str | None = None) -> str:
    """Initialize a new ike.md project in a directory. Creates the .ike/ folder structure and ike.json with a stable GUID. Returns the project_id for use in all subsequent calls."""
    config = init_project(path, name)
    # Register it for this session
    try:
        register_project(os.path.abspath(path))
    except Exception:
        pass
    return f"Project initialized: **{config.project}**\nproject_id: `{config.id}`\nPath: {path}\n\nUse this project_id in all subsequent calls."


@mcp.tool()
def project_set(path: str) -> str:
    """Register an existing ike.md project for this session. Call this at session start. Returns the project_id (GUID) to use in all subsequent calls."""
    result = register_project(path)
    return f"Project registered: **{result['project']}**\nproject_id: `{result['id']}`\n\nUse this project_id in all subsequent calls."


@mcp.tool()
def project_list() -> str:
    """List all projects registered in this session."""
    projects = list_registered()
    if not projects:
        return "No projects registered this session. Call project_set with a project path."
    return "\n".join(f"- `{p['id']}` → {p['path']}" for p in projects)


@mcp.tool()
def project_info(project_id: str) -> str:
    """Show project stats: task counts by status, milestone summary, document count. Call this at session start to orient yourself."""
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
    status_line = " · ".join(f"{s}: {n}" for s, n in counts.items()) or "none"
    lines = [
        f"## {name}",
        f"project_id: `{project_id}`",
        f"Path: {project_root}",
        "",
        f"**Tasks:** {status_line}",
        f"**Milestones:** {open_ms} open, {len(milestones) - open_ms} closed",
        f"**Documents:** {len(docs)}",
    ]
    return "\n".join(lines)


# ── Tasks ─────────────────────────────────────────────────────────────────────


@mcp.tool()
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
        "created": _today(),
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


@mcp.tool()
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
        blocked = f" — BLOCKED: {fm['blocked_reason']}" if fm.get("blocked_reason") else ""
        lines.append(f"{badge} **{fm['id']}**{pri} — {fm['title']}{blocked}")
    return "\n".join(lines)


@mcp.tool()
def task_view(project_id: str, task_id: str) -> str:
    """View a task in full detail by ID."""
    project_root = resolve_project(project_id)
    fp = find_task_file(project_root, task_id)
    if not fp:
        return f"Task {task_id} not found."
    task = read_markdown(fp)
    return _format_task(task.frontmatter, task.content)


@mcp.tool()
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
    """Edit a task's fields. Only provided fields are updated."""
    project_root = resolve_project(project_id)
    fp = find_task_file(project_root, task_id)
    if not fp:
        return f"Task {task_id} not found."
    task = read_markdown(fp)
    fm = {**task.frontmatter, "updated": _today()}
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


@mcp.tool()
def task_complete(project_id: str, task_id: str, notes: str | None = None) -> str:
    """Mark a task as Done and move it to the completed folder."""
    project_root = resolve_project(project_id)
    fp = find_task_file(project_root, task_id)
    if not fp:
        return f"Task {task_id} not found."
    task = read_markdown(fp)
    fm = {**task.frontmatter, "status": "Done", "updated": _today()}
    content = f"{task.content}\n\n**Completion notes:** {notes}".strip() if notes else task.content
    dest = task_path(project_root, fm["id"], fm["title"], completed=True)
    write_markdown(dest, fm, content)
    os.unlink(fp)
    return f"Completed **{fm['id']}** — {fm['title']}\nMoved to completed/"


@mcp.tool()
def task_archive(project_id: str, task_id: str, reason: str | None = None) -> str:
    """Archive a task (cancelled, duplicate, or invalid)."""
    project_root = resolve_project(project_id)
    fp = find_task_file(project_root, task_id)
    if not fp:
        return f"Task {task_id} not found."
    task = read_markdown(fp)
    fm = {**task.frontmatter, "updated": _today()}
    content = f"{task.content}\n\n**Archived:** {reason}".strip() if reason else task.content
    archive_path = safe_path(project_root, IKE_DIR, DIRECTORIES["ARCHIVE"], os.path.basename(fp))
    write_markdown(archive_path, fm, content)
    os.unlink(fp)
    return f"Archived **{fm['id']}** — {fm['title']}"


@mcp.tool()
def task_search(project_id: str, query: str, include_completed: bool = False) -> str:
    """Search tasks by keyword in title and description."""
    project_root = resolve_project(project_id)
    tasks = list_all_tasks(project_root) if include_completed else list_tasks(project_root, False)
    q = query.lower()
    matches = [
        t for t in tasks
        if q in t.frontmatter["title"].lower() or q in t.content.lower()
    ]
    if not matches:
        return f'No tasks matching "{query}".'
    return "\n".join(
        f"**{t.frontmatter['id']}** — {t.frontmatter['title']} [{t.frontmatter['status']}]"
        for t in matches
    )


# ── Milestones ────────────────────────────────────────────────────────────────


@mcp.tool()
def milestone_create(project_id: str, title: str, description: str = "", due: str | None = None) -> str:
    """Create a new milestone."""
    project_root = resolve_project(project_id)
    id = next_milestone_id(project_root)
    fm: dict = {"id": id, "title": title, "status": "open", "created": _today()}
    if due:
        fm["due"] = due
    write_markdown(milestone_path(project_root, id, title), fm, description)
    return f"Created milestone **{id}** — {title}"


@mcp.tool()
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


@mcp.tool()
def milestone_view(project_id: str, milestone_id: str) -> str:
    """View a milestone in full detail by ID."""
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


@mcp.tool()
def milestone_close(project_id: str, milestone_id: str, notes: str | None = None) -> str:
    """Close a milestone (mark it complete)."""
    project_root = resolve_project(project_id)
    fp = find_milestone_file(project_root, milestone_id)
    if not fp:
        return f"Milestone {milestone_id} not found."
    m = read_markdown(fp)
    fm = {**m.frontmatter, "status": "closed"}
    content = f"{m.content}\n\n**Closed:** {notes}".strip() if notes else m.content
    write_markdown(fp, fm, content)
    return f"Closed milestone **{fm['id']}** — {fm['title']}"


# ── Documents ─────────────────────────────────────────────────────────────────


@mcp.tool()
def document_create(project_id: str, title: str, content: str = "", tags: list[str] | None = None) -> str:
    """Create a project document."""
    project_root = resolve_project(project_id)
    id = next_document_id(project_root)
    fm: dict = {"id": id, "title": title, "created": _today()}
    if tags:
        fm["tags"] = tags
    write_markdown(document_path(project_root, id, title), fm, content)
    return f"Created document **{id}** — {title}"


@mcp.tool()
def document_list(project_id: str) -> str:
    """List all documents."""
    project_root = resolve_project(project_id)
    docs = list_documents(project_root)
    if not docs:
        return "No documents."
    return "\n".join(f"**{d.frontmatter['id']}** — {d.frontmatter['title']}" for d in docs)


@mcp.tool()
def document_view(project_id: str, document_id: str) -> str:
    """View a document by ID."""
    project_root = resolve_project(project_id)
    fp = find_document_file(project_root, document_id)
    if not fp:
        return f"Document {document_id} not found."
    doc = read_markdown(fp)
    return f"## {doc.frontmatter['id']} — {doc.frontmatter['title']}\n\n{doc.content}"


@mcp.tool()
def document_update(
    project_id: str,
    document_id: str,
    title: str | None = None,
    content: str | None = None,
    tags: list[str] | None = None,
    append_content: str | None = None,
) -> str:
    """Update a document's content or tags. Only provided fields are changed."""
    project_root = resolve_project(project_id)
    fp = find_document_file(project_root, document_id)
    if not fp:
        return f"Document {document_id} not found."
    doc = read_markdown(fp)
    fm = {**doc.frontmatter, "updated": _today()}
    if title is not None:
        fm["title"] = title
    if tags is not None:
        fm["tags"] = tags
    if append_content:
        new_content = f"{doc.content}\n\n{append_content}".strip()
    elif content is not None:
        new_content = content
    else:
        new_content = doc.content
    write_markdown(fp, fm, new_content)
    return f"Updated **{fm['id']}** — {fm['title']}"


def main():
    mcp.run()
