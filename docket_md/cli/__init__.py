"""docket-md Typer CLI surface.

``docket-md <subcommand> [--json] [opts]`` — everything is here. The MCP
server (``docket_md.mcp_server``) exposes a single ``help`` tool that
introspects this Typer app.
"""

from ._app import app, main

__all__ = ["app", "main"]
