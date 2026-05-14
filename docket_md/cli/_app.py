"""Typer root + shared output formatter for docket-md."""

from __future__ import annotations

import json as _json

import typer

app = typer.Typer(
    name="docket-md",
    help="docket.md — the execution forge. Tasks, milestones, documents, Definition of Done.",
    no_args_is_help=True,
    add_completion=False,
)


@app.callback()
def _root_callback() -> None:
    """Auto-register any docket project rooted at or above CWD before each command."""
    from .._logic._session import boot_from_cwd

    boot_from_cwd()


def emit(result, *, json_mode: bool) -> None:
    """Print a result. JSON mode dumps; otherwise the original string is preserved."""
    if json_mode:
        typer.echo(_json.dumps(result, indent=2, default=str))
        return
    if isinstance(result, str):
        typer.echo(result)
    elif isinstance(result, (dict, list)):
        typer.echo(_json.dumps(result, indent=2, default=str))
    else:
        typer.echo(str(result))


def _wire() -> None:
    from . import bookmark as _bookmark_cmd
    from . import config as _config_cmd
    from . import document as _document_cmd
    from . import graph as _graph_cmd
    from . import mcp as _mcp_cmd
    from . import milestone as _milestone_cmd
    from . import plan as _plan_cmd
    from . import project as _project_cmd
    from . import task as _task_cmd

    _project_cmd.register(app)
    _task_cmd.register(app)
    _milestone_cmd.register(app)
    _document_cmd.register(app)
    _graph_cmd.register(app)
    _plan_cmd.register(app)
    _config_cmd.register(app)
    _bookmark_cmd.register(app)
    app.add_typer(_mcp_cmd.app, name="mcp", help="MCP server operations.")


_wire()


def main() -> None:
    """Console-script entry point (``docket-md``)."""
    app()
