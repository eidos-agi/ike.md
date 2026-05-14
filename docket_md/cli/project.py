"""Project lifecycle subcommands."""

from __future__ import annotations

from typing import Annotated, Optional

import typer

from .._logic import project as _project


def register(app: typer.Typer) -> None:
    @app.command("project-init")
    def cmd_project_init(
        path: Annotated[str, typer.Argument(help="Directory to initialize.")],
        name: Annotated[
            Optional[str], typer.Option(help="Project display name.")
        ] = None,
        json_: Annotated[
            bool, typer.Option("--json", "-J", help="JSON output.")
        ] = False,
    ) -> None:
        """Initialize a new docket.md project."""
        from ._app import emit

        result = _project.project_init(path=path, name=name)
        emit(result, json_mode=json_)

    @app.command("project-set")
    def cmd_project_set(
        path: Annotated[str, typer.Argument(help="Path to an existing project.")],
        json_: Annotated[
            bool, typer.Option("--json", "-J", help="JSON output.")
        ] = False,
    ) -> None:
        """Register an existing project for this session."""
        from ._app import emit

        result = _project.project_set(path)
        emit(result, json_mode=json_)

    @app.command("project-list")
    def cmd_project_list(
        json_: Annotated[
            bool, typer.Option("--json", "-J", help="JSON output.")
        ] = False,
    ) -> None:
        """List all projects registered in this session."""
        from ._app import emit

        result = _project.project_list()
        emit(result, json_mode=json_)

    @app.command("project-info")
    def cmd_project_info(
        project_id: Annotated[str, typer.Option(help="Project GUID.")],
        json_: Annotated[
            bool, typer.Option("--json", "-J", help="JSON output.")
        ] = False,
    ) -> None:
        """Show project stats."""
        from ._app import emit

        result = _project.project_info(project_id=project_id)
        emit(result, json_mode=json_)
