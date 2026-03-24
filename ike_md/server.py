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
    graph_node_path,
    read_graph_node,
    write_graph_node,
    list_graph_nodes,
    find_graph_node_file,
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


# ── Graph ────────────────────────────────────────────────────────────────────


@mcp.tool()
def graph_create_node(
    project_id: str,
    node_id: str,
    node_type: str,
    title: str,
    attributes: dict | None = None,
    edges: list[dict] | None = None,
) -> str:
    """Create a graph node. Nodes represent people, emails, artifacts, deadlines, Wrike cards, or projects.

    Args:
        project_id: The project GUID
        node_id: Unique ID for the node (e.g., 'person/suman-panda', 'wrike/scr-001')
        node_type: Type of node (person, email, artifact, deadline, wrike_card, project, repo)
        title: Human-readable title
        attributes: Optional dict of additional attributes
        edges: Optional list of edges, each with 'type' and 'target' keys
    """
    project_root = resolve_project(project_id)
    fp = graph_node_path(project_root, node_id)
    if os.path.exists(fp):
        return f"Node `{node_id}` already exists. Use graph_add_edge to add connections."

    data: dict = {
        "id": node_id,
        "type": node_type,
        "title": title,
        "created": _today(),
    }
    if attributes:
        data["attributes"] = attributes
    if edges:
        data["edges"] = edges

    write_graph_node(fp, data)
    edge_count = len(edges) if edges else 0
    return f"Created graph node `{node_id}` ({node_type}) — {title}\nEdges: {edge_count}\nFile: {fp}"


@mcp.tool()
def graph_get_node(project_id: str, node_id: str) -> str:
    """Read a graph node by ID. Returns all attributes and edges.

    Args:
        project_id: The project GUID
        node_id: The node ID to retrieve
    """
    project_root = resolve_project(project_id)
    fp = find_graph_node_file(project_root, node_id)
    if not fp:
        return f"Node `{node_id}` not found."

    data = read_graph_node(fp)
    lines = [
        f"## {data.get('title', node_id)}",
        f"**ID:** `{data.get('id', node_id)}`",
        f"**Type:** {data.get('type', 'unknown')}",
    ]
    if data.get("created"):
        lines.append(f"**Created:** {data['created']}")

    attrs = data.get("attributes", {})
    if attrs:
        lines.append("\n**Attributes:**")
        for k, v in attrs.items():
            lines.append(f"  {k}: {v}")

    edges = data.get("edges", [])
    if edges:
        lines.append(f"\n**Edges ({len(edges)}):**")
        for e in edges:
            lines.append(f"  —[{e.get('type', '?')}]→ `{e.get('target', '?')}`")
    else:
        lines.append("\n**Edges:** none")

    return "\n".join(lines)


@mcp.tool()
def graph_add_edge(
    project_id: str,
    source_node_id: str,
    edge_type: str,
    target_node_id: str,
) -> str:
    """Add a typed edge from one node to another.

    Args:
        project_id: The project GUID
        source_node_id: The node to add the edge FROM
        edge_type: Relationship type (e.g., 'approver', 'vendor', 'artifact', 'due_by', 'subproject', 'email_thread')
        target_node_id: The node to add the edge TO
    """
    project_root = resolve_project(project_id)
    fp = find_graph_node_file(project_root, source_node_id)
    if not fp:
        return f"Source node `{source_node_id}` not found."

    data = read_graph_node(fp)
    edges = data.get("edges", [])

    # Check for duplicate
    for e in edges:
        if e.get("type") == edge_type and e.get("target") == target_node_id:
            return f"Edge already exists: `{source_node_id}` —[{edge_type}]→ `{target_node_id}`"

    edges.append({"type": edge_type, "target": target_node_id})
    data["edges"] = edges
    write_graph_node(fp, data)
    return f"Added edge: `{source_node_id}` —[{edge_type}]→ `{target_node_id}`"


@mcp.tool()
def graph_list_nodes(
    project_id: str,
    node_type: str | None = None,
    query: str | None = None,
) -> str:
    """List graph nodes with optional filtering by type or keyword search.

    Args:
        project_id: The project GUID
        node_type: Filter by node type (person, email, artifact, deadline, wrike_card, project)
        query: Search keyword — matches node ID, title, and attribute values
    """
    project_root = resolve_project(project_id)
    nodes = list_graph_nodes(project_root)

    if node_type:
        nodes = [n for n in nodes if n.get("type") == node_type]

    if query:
        q = query.lower()

        def _matches(node: dict) -> bool:
            if q in node.get("id", "").lower():
                return True
            if q in node.get("title", "").lower():
                return True
            for v in node.get("attributes", {}).values():
                if q in str(v).lower():
                    return True
            return False

        nodes = [n for n in nodes if _matches(n)]

    if not nodes:
        return "No graph nodes found."

    lines = []
    for n in nodes:
        edge_count = len(n.get("edges", []))
        edges_str = f" ({edge_count} edges)" if edge_count else ""
        lines.append(f"• `{n['id']}` [{n.get('type', '?')}] — {n.get('title', '(untitled)')}{edges_str}")

    return f"**{len(lines)} nodes:**\n" + "\n".join(lines)


@mcp.tool()
def graph_traverse(
    project_id: str,
    node_id: str,
    depth: int = 1,
) -> str:
    """Follow all edges from a node and return the full connected subgraph in one call.

    Returns the starting node plus all nodes reachable within the given depth,
    with their attributes and edges. Executable references (aic_mail_query,
    wrike_id, path) are highlighted for the agent to act on.

    Args:
        project_id: The project GUID
        node_id: The starting node ID
        depth: How many hops to follow (default 1 = direct connections only)
    """
    project_root = resolve_project(project_id)

    # Load starting node
    fp = find_graph_node_file(project_root, node_id)
    if not fp:
        return f"Node `{node_id}` not found."

    root = read_graph_node(fp)
    visited: dict[str, dict] = {node_id: root}
    frontier = [(node_id, 0)]

    # BFS traversal
    while frontier:
        current_id, current_depth = frontier.pop(0)
        if current_depth >= depth:
            continue
        node = visited[current_id]
        for edge in node.get("edges", []):
            target_id = edge.get("target", "")
            if target_id not in visited:
                tfp = find_graph_node_file(project_root, target_id)
                if tfp:
                    target_data = read_graph_node(tfp)
                    visited[target_id] = target_data
                    frontier.append((target_id, current_depth + 1))

    # Format output
    lines = []

    # Root node header
    attrs = root.get("attributes", {})
    status = attrs.get("status", "")
    deadline = attrs.get("deadline", "")
    header = f"## {root.get('title', node_id)}"
    if status or deadline:
        meta = " | ".join(filter(None, [
            f"Status: {status}" if status else "",
            f"Deadline: {deadline}" if deadline else "",
        ]))
        header += f"\n{meta}"
    lines.append(header)

    # Connected nodes
    edges = root.get("edges", [])
    if edges:
        lines.append(f"\n**CONNECTED ({len(edges)}):**")
        for edge in edges:
            target_id = edge.get("target", "?")
            edge_type = edge.get("type", "?")
            target = visited.get(target_id)
            if target:
                tattrs = target.get("attributes", {})
                detail_parts = []
                # Pick the most useful attributes to show inline
                for key in ("role", "email", "status", "date", "consequence", "path",
                            "aic_mail_query", "wrike_id", "hard"):
                    if key in tattrs:
                        detail_parts.append(f"{key}: {tattrs[key]}")
                detail = " | ".join(detail_parts) if detail_parts else ""
                detail_str = f" ({detail})" if detail else ""
                lines.append(f"  —[{edge_type}]→ **{target.get('title', target_id)}**{detail_str}")
            else:
                lines.append(f"  —[{edge_type}]→ `{target_id}` (not found in graph)")

    # Executable references
    exec_refs = []
    for nid, node in visited.items():
        if nid == node_id:
            continue
        na = node.get("attributes", {})
        if na.get("aic_mail_query"):
            exec_refs.append(f"  aic-mail: mail_search(\"{na['aic_mail_query']}\")")
            if na.get("outbound_id"):
                exec_refs.append(f"  aic-mail: mail_read({na['outbound_id']})")
        if na.get("wrike_id"):
            exec_refs.append(f"  wrike: get_task(\"{na['wrike_id']}\")")
        if na.get("path"):
            exec_refs.append(f"  file: {na['path']}")

    if exec_refs:
        lines.append(f"\n**EXECUTABLE REFERENCES:**")
        lines.extend(exec_refs)

    return "\n".join(lines)


def main():
    mcp.run()
