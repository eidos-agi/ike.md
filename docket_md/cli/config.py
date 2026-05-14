"""Config subcommands."""

from __future__ import annotations

from typing import Annotated, Optional

import typer

from .._logic import config as _config


def register(app: typer.Typer) -> None:
    @app.command("config-get")
    def cmd_config_get(
        project_id: Annotated[Optional[str], typer.Option(help="Project GUID.")] = None,
        path: Annotated[Optional[str], typer.Option(help="Project path.")] = None,
        json_: Annotated[
            bool, typer.Option("--json", "-J", help="JSON output.")
        ] = False,
    ) -> None:
        """Show resolved settings with inheritance visible."""
        from ._app import emit

        result = _config.config_get(project_id=project_id, path=path)
        emit(result, json_mode=json_)

    @app.command("config-set")
    def cmd_config_set(
        key: Annotated[str, typer.Option(help="Setting key (dot notation supported).")],
        value: Annotated[str, typer.Option(help="Value (JSON-parsed if possible).")],
        level: Annotated[
            str, typer.Option(help="global | org | repo | project.")
        ] = "project",
        project_id: Annotated[Optional[str], typer.Option(help="Project GUID.")] = None,
        path: Annotated[Optional[str], typer.Option(help="Project path.")] = None,
        json_: Annotated[
            bool, typer.Option("--json", "-J", help="JSON output.")
        ] = False,
    ) -> None:
        """Set a config value at a specific level."""
        from ._app import emit

        result = _config.config_set(
            key=key,
            value=value,
            level=level,
            project_id=project_id,
            path=path,
        )
        emit(result, json_mode=json_)

    @app.command("config-tree")
    def cmd_config_tree(
        json_: Annotated[
            bool, typer.Option("--json", "-J", help="JSON output.")
        ] = False,
    ) -> None:
        """Show the entire ~/.config/docket/ settings tree."""
        from ._app import emit

        result = _config.config_tree()
        emit(result, json_mode=json_)

    @app.command("config-where")
    def cmd_config_where(
        key: Annotated[str, typer.Argument(help="Setting key (dot notation).")],
        project_id: Annotated[Optional[str], typer.Option(help="Project GUID.")] = None,
        path: Annotated[Optional[str], typer.Option(help="Project path.")] = None,
        json_: Annotated[
            bool, typer.Option("--json", "-J", help="JSON output.")
        ] = False,
    ) -> None:
        """Show which level set a specific config key."""
        from ._app import emit

        result = _config.config_where(key=key, project_id=project_id, path=path)
        emit(result, json_mode=json_)
