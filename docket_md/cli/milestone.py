"""Milestone subcommands."""

from __future__ import annotations

from typing import Annotated, Optional

import typer

from .._logic import milestone as _milestone


def register(app: typer.Typer) -> None:
    @app.command("milestone-create")
    def cmd_milestone_create(
        project_id: Annotated[str, typer.Option(help="Project GUID.")],
        title: Annotated[str, typer.Option(help="Milestone title.")],
        description: Annotated[str, typer.Option(help="Description.")] = "",
        due: Annotated[Optional[str], typer.Option(help="Due date (ISO).")] = None,
        json_: Annotated[
            bool, typer.Option("--json", "-J", help="JSON output.")
        ] = False,
    ) -> None:
        """Create a new milestone."""
        from ._app import emit

        result = _milestone.milestone_create(
            project_id=project_id, title=title, description=description, due=due
        )
        emit(result, json_mode=json_)

    @app.command("milestone-list")
    def cmd_milestone_list(
        project_id: Annotated[str, typer.Option(help="Project GUID.")],
        json_: Annotated[
            bool, typer.Option("--json", "-J", help="JSON output.")
        ] = False,
    ) -> None:
        """List all milestones."""
        from ._app import emit

        result = _milestone.milestone_list(project_id=project_id)
        emit(result, json_mode=json_)

    @app.command("milestone-view")
    def cmd_milestone_view(
        project_id: Annotated[str, typer.Option(help="Project GUID.")],
        milestone_id: Annotated[str, typer.Argument(help="Milestone ID.")],
        json_: Annotated[
            bool, typer.Option("--json", "-J", help="JSON output.")
        ] = False,
    ) -> None:
        """View a milestone in full detail."""
        from ._app import emit

        result = _milestone.milestone_view(
            project_id=project_id, milestone_id=milestone_id
        )
        emit(result, json_mode=json_)

    @app.command("milestone-close")
    def cmd_milestone_close(
        project_id: Annotated[str, typer.Option(help="Project GUID.")],
        milestone_id: Annotated[str, typer.Argument(help="Milestone ID.")],
        notes: Annotated[Optional[str], typer.Option(help="Closing notes.")] = None,
        json_: Annotated[
            bool, typer.Option("--json", "-J", help="JSON output.")
        ] = False,
    ) -> None:
        """Close a milestone."""
        from ._app import emit

        result = _milestone.milestone_close(
            project_id=project_id, milestone_id=milestone_id, notes=notes
        )
        emit(result, json_mode=json_)
