"""Graph CRUD: create-node, get-node, add-edge, list-nodes, traverse."""

from __future__ import annotations

import os

from ..config import resolve_project
from ..files import (
    find_graph_node_file,
    graph_node_path,
    list_graph_nodes,
    read_graph_node,
    write_graph_node,
)
from ._common import today


def graph_create_node(
    project_id: str,
    node_id: str,
    node_type: str,
    title: str,
    attributes: dict | None = None,
    edges: list[dict] | None = None,
) -> str:
    """Create a graph node."""
    project_root = resolve_project(project_id)
    fp = graph_node_path(project_root, node_id)
    if os.path.exists(fp):
        return (
            f"Node `{node_id}` already exists. Use graph_add_edge to add connections."
        )

    data: dict = {
        "id": node_id,
        "type": node_type,
        "title": title,
        "created": today(),
    }
    if attributes:
        data["attributes"] = attributes
    if edges:
        data["edges"] = edges

    write_graph_node(fp, data)
    edge_count = len(edges) if edges else 0
    return (
        f"Created graph node `{node_id}` ({node_type}) — {title}\n"
        f"Edges: {edge_count}\nFile: {fp}"
    )


def graph_get_node(project_id: str, node_id: str) -> str:
    """Read a graph node by ID."""
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


def graph_add_edge(
    project_id: str,
    source_node_id: str,
    edge_type: str,
    target_node_id: str,
) -> str:
    """Add a typed edge from one node to another."""
    project_root = resolve_project(project_id)
    fp = find_graph_node_file(project_root, source_node_id)
    if not fp:
        return f"Source node `{source_node_id}` not found."

    data = read_graph_node(fp)
    edges = data.get("edges", [])

    for e in edges:
        if e.get("type") == edge_type and e.get("target") == target_node_id:
            return f"Edge already exists: `{source_node_id}` —[{edge_type}]→ `{target_node_id}`"

    edges.append({"type": edge_type, "target": target_node_id})
    data["edges"] = edges
    write_graph_node(fp, data)
    return f"Added edge: `{source_node_id}` —[{edge_type}]→ `{target_node_id}`"


def graph_list_nodes(
    project_id: str,
    node_type: str | None = None,
    query: str | None = None,
) -> str:
    """List graph nodes with optional filtering."""
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
        lines.append(
            f"• `{n['id']}` [{n.get('type', '?')}] — {n.get('title', '(untitled)')}{edges_str}"
        )

    return f"**{len(lines)} nodes:**\n" + "\n".join(lines)


def graph_traverse(
    project_id: str,
    node_id: str,
    depth: int = 1,
) -> str:
    """Follow all edges from a node and return the connected subgraph."""
    project_root = resolve_project(project_id)

    fp = find_graph_node_file(project_root, node_id)
    if not fp:
        return f"Node `{node_id}` not found."

    root = read_graph_node(fp)
    visited: dict[str, dict] = {node_id: root}
    frontier = [(node_id, 0)]

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

    lines = []

    attrs = root.get("attributes", {})
    status = attrs.get("status", "")
    deadline = attrs.get("deadline", "")
    header = f"## {root.get('title', node_id)}"
    if status or deadline:
        meta = " | ".join(
            filter(
                None,
                [
                    f"Status: {status}" if status else "",
                    f"Deadline: {deadline}" if deadline else "",
                ],
            )
        )
        header += f"\n{meta}"
    lines.append(header)

    def _format_edge(source_id: str, edge: dict, indent: str) -> None:
        target_id = edge.get("target", "?")
        edge_type = edge.get("type", "?")
        target = visited.get(target_id)
        if target:
            tattrs = target.get("attributes", {})
            detail_parts = []
            for key in (
                "role",
                "email",
                "status",
                "date",
                "consequence",
                "path",
                "aic_mail_query",
                "wrike_id",
                "hard",
            ):
                if key in tattrs:
                    detail_parts.append(f"{key}: {tattrs[key]}")
            detail = " | ".join(detail_parts) if detail_parts else ""
            detail_str = f" ({detail})" if detail else ""
            lines.append(
                f"{indent}—[{edge_type}]→ **{target.get('title', target_id)}**{detail_str}"
            )
        else:
            lines.append(f"{indent}—[{edge_type}]→ `{target_id}` (not found in graph)")

    # BFS-printed subgraph. We re-walk to preserve insertion order and indent
    # by depth so the agent can see chains, not just root's first-hop.
    printed: set[str] = {node_id}
    visit_frontier: list[tuple[str, int]] = [(node_id, 0)]
    total_edges_shown = 0
    while visit_frontier:
        src_id, src_depth = visit_frontier.pop(0)
        if src_depth >= depth:
            continue
        src_node = visited.get(src_id)
        if not src_node:
            continue
        src_edges = src_node.get("edges", [])
        if not src_edges:
            continue
        if src_id == node_id:
            lines.append(f"\n**CONNECTED ({len(src_edges)}):**")
        else:
            lines.append(
                f"\n**from `{src_id}` ({src_node.get('title', '?')}):**"
            )
        indent = "  " * (src_depth + 1)
        for edge in src_edges:
            _format_edge(src_id, edge, indent)
            total_edges_shown += 1
            target_id = edge.get("target", "")
            if target_id and target_id not in printed and target_id in visited:
                printed.add(target_id)
                visit_frontier.append((target_id, src_depth + 1))

    exec_refs = []
    for nid, node in visited.items():
        if nid == node_id:
            continue
        na = node.get("attributes", {})
        if na.get("aic_mail_query"):
            exec_refs.append(f'  aic-mail: mail_search("{na["aic_mail_query"]}")')
            if na.get("outbound_id"):
                exec_refs.append(f"  aic-mail: mail_read({na['outbound_id']})")
        if na.get("wrike_id"):
            exec_refs.append(f'  wrike: get_task("{na["wrike_id"]}")')
        if na.get("path"):
            exec_refs.append(f"  file: {na['path']}")

    if exec_refs:
        lines.append("\n**EXECUTABLE REFERENCES:**")
        lines.extend(exec_refs)

    return "\n".join(lines)
