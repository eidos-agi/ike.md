"""Razor-thin MCP server for docket-md.

Exposes ONE tool: ``help``. Every other operation happens via the CLI
(``docket-md task-create``, ``docket-md plan-list``, etc.). This is the
CLI-first / razor-thin-MCP shape — see ADR-006 in governor.md/.governor/adr/.

Discovery flow:
  1. Agent calls ``mcp__docket-md__help()`` — gets the full command tree.
  2. Agent calls ``mcp__docket-md__help(subcommand="task-create")`` —
     gets that subcommand's full --help output.
  3. Agent invokes the actual work via Bash:
     ``docket-md task-create ... --json``.
"""

from __future__ import annotations

import asyncio
import io
import sys

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

server = Server("docket-md")


HELP_DESCRIPTION = (
    "REQUIRED at session start for any docket-md work: returns the full "
    "docket-md command tree. Call with no args for the top-level surface, "
    "or with subcommand='<name>' for that subcommand's full --help. All "
    "real work happens via Bash: `docket-md <subcommand> [--json] [opts]`. "
    "Start every session with `docket-md project-info` after project-set "
    "to orient. This MCP server is razor-thin by design."
)


HELP_TOOL = Tool(
    name="help",
    description=HELP_DESCRIPTION,
    inputSchema={
        "type": "object",
        "properties": {
            "subcommand": {
                "type": "string",
                "description": (
                    "Optional subcommand name (e.g. 'task-create', "
                    "'milestone-close', 'plan-update'). When set, returns "
                    "that subcommand's full --help. When omitted, returns "
                    "the top-level command tree."
                ),
            },
        },
    },
)


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [HELP_TOOL]


def _capture_help(argv: list[str]) -> str:
    from .cli import app

    buf = io.StringIO()
    real_stdout = sys.stdout
    sys.stdout = buf
    try:
        try:
            app(argv, standalone_mode=False)
        except SystemExit:
            pass
        except Exception as e:
            return f"error rendering help: {type(e).__name__}: {e}"
    finally:
        sys.stdout = real_stdout
    return buf.getvalue()


def _build_top_level_help() -> str:
    return "\n".join(
        [
            "docket-md — The execution forge. Tasks, milestones, documents, Definition of Done.",
            "",
            "USAGE:  docket-md <subcommand> [--json] [options]",
            "",
            "SESSION START:",
            "  docket-md project-set <path>             # register, returns project_id",
            "  docket-md project-info --project-id <id> # one-line orient",
            "",
            "PROJECTS:",
            "  docket-md project-init <path>            # initialize a new project",
            "  docket-md project-list                   # list registered projects",
            "",
            "TASKS:",
            "  docket-md task-create                    # new task",
            "  docket-md task-list                      # list (filter by status/milestone/...)",
            "  docket-md task-view <id>                 # full task detail",
            "  docket-md task-edit <id>                 # update fields",
            "  docket-md task-complete <id>             # mark Done; move to completed/",
            "  docket-md task-archive <id>              # archive",
            "  docket-md task-search <query>            # keyword search",
            "",
            "MILESTONES:",
            "  docket-md milestone-create               # new milestone",
            "  docket-md milestone-list                 # list",
            "  docket-md milestone-view <id>            # full detail",
            "  docket-md milestone-close <id>           # close",
            "",
            "DOCUMENTS:",
            "  docket-md document-create                # new project doc",
            "  docket-md document-list                  # list",
            "  docket-md document-view <id>             # read",
            "  docket-md document-update <id>           # update",
            "",
            "GRAPH (people/emails/artifacts/deadlines):",
            "  docket-md graph-create-node              # new node",
            "  docket-md graph-get-node <id>            # read node + edges",
            "  docket-md graph-add-edge                 # add typed edge",
            "  docket-md graph-list-nodes               # list (filter by type/keyword)",
            "  docket-md graph-traverse <id>            # BFS subgraph + executable refs",
            "",
            "PLANS:",
            "  docket-md plan-create                    # new plan",
            "  docket-md plan-list                      # list",
            "  docket-md plan-view <id>                 # full detail",
            "  docket-md plan-update <id>               # update",
            "  docket-md plan-verify <id>               # checklist of verification criteria",
            "",
            "CONFIG (hierarchical inheritance: global → org → repo → project):",
            "  docket-md config-get                     # resolved settings + chain",
            "  docket-md config-set                     # set a key at a level",
            "  docket-md config-tree                    # whole ~/.config/docket/ tree",
            "  docket-md config-where <key>             # show which level set a key",
            "",
            "BOOKMARK:",
            "  docket-md bookmark                       # timestamped checkpoint + optional Wrike sync",
            "",
            "MCP:",
            "  docket-md mcp serve                      # boots this MCP server (you're talking to it now)",
            "",
            "DRILL IN:    docket-md <subcommand> --help    "
            "OR    mcp__docket-md__help(subcommand='<name>')",
            "JSON MODE:   add --json to any subcommand for machine-readable output",
        ]
    )


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name != "help":
        return [TextContent(type="text", text=f"unknown tool: {name!r}")]
    sub = (arguments or {}).get("subcommand")
    if sub:
        text = _capture_help([sub, "--help"])
        if not text.strip():
            text = f"no help available for subcommand {sub!r}"
        return [TextContent(type="text", text=text)]
    return [TextContent(type="text", text=_build_top_level_help())]


async def _main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, write_stream, server.create_initialization_options()
        )


def run() -> None:
    """Entry point used by ``docket-md mcp serve``."""
    try:
        asyncio.run(_main())
    except KeyboardInterrupt:
        sys.exit(0)
