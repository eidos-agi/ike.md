"""docket.md MCP server — thin shim over ``docket_md._logic``.

Stage A (CLI-first refactor): all 34 tool bodies have moved to ``_logic/``;
this file imports them and registers them with FastMCP. Stage B will
collapse the surface to a single ``help`` tool (see ADR-006 in governor.md).
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from ._logic.bookmark import bookmark
from ._logic.config import config_get, config_set, config_tree, config_where
from ._logic.document import (
    document_create,
    document_list,
    document_update,
    document_view,
)
from ._logic.graph import (
    graph_add_edge,
    graph_create_node,
    graph_get_node,
    graph_list_nodes,
    graph_traverse,
)
from ._logic.milestone import (
    milestone_close,
    milestone_create,
    milestone_list,
    milestone_view,
)
from ._logic.plan import (
    plan_create,
    plan_list,
    plan_update,
    plan_verify,
    plan_view,
)
from ._logic.project import project_info, project_init, project_list, project_set
from ._logic.task import (
    task_archive,
    task_complete,
    task_create,
    task_edit,
    task_list,
    task_search,
    task_view,
)

INSTRUCTIONS = """docket.md is the execution forge — tasks, milestones, documents, Definition of Done. This is where work gets done.

Named for a court's docket: the queue of cases ready for resolution. Planning happens elsewhere; the docket is where work gets scheduled, dispatched, and closed. (Previously codenamed `ike`, after Eisenhower — same discipline, different metaphor.)

READ visionlog at the start of every session before touching anything. visionlog is the static St. Peter: it tells you where the ladder points, what the project has committed to, and what guardrails you must not cross. If a task would violate a visionlog guardrail, St. Peter has already told you no — adjust before you start.

Before making a consequential decision that spawns tasks, use research.md to earn that decision with evidence. Then record it in visionlog as an ADR. Then create tasks here to execute it.

The trilogy:
- research.md: decide with evidence
- visionlog: record vision, goals, guardrails, SOPs, ADRs — the contracts all execution must honor
- docket.md: execute within those contracts — this is where you are now

GUID workflow: Call project_set with the project path to register it and get its project_id. Pass that project_id to every subsequent tool call. For a new project, call project_init first."""

mcp = FastMCP("docket.md", instructions=INSTRUCTIONS)


for fn in (
    project_init,
    project_set,
    project_list,
    project_info,
    task_create,
    task_list,
    task_view,
    task_edit,
    task_complete,
    task_archive,
    task_search,
    milestone_create,
    milestone_list,
    milestone_view,
    milestone_close,
    document_create,
    document_list,
    document_view,
    document_update,
    graph_create_node,
    graph_get_node,
    graph_add_edge,
    graph_list_nodes,
    graph_traverse,
    plan_create,
    plan_list,
    plan_view,
    plan_update,
    plan_verify,
    config_get,
    config_set,
    config_tree,
    config_where,
    bookmark,
):
    mcp.tool()(fn)


def main():
    mcp.run()
