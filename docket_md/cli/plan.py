"""Plan subcommands."""

from __future__ import annotations

from typing import Annotated, Optional

import typer

from .._logic import plan as _plan
from ._helpers import parse_str_list


def register(app: typer.Typer) -> None:
    @app.command("plan-create")
    def cmd_plan_create(
        project_id: Annotated[str, typer.Option(help="Project GUID.")],
        title: Annotated[str, typer.Option(help="Plan title.")],
        content: Annotated[str, typer.Option(help="Plan content.")] = "",
        tags: Annotated[
            Optional[str], typer.Option("--tags", help="JSON array of tags.")
        ] = None,
        verification: Annotated[
            Optional[str],
            typer.Option(
                "--verification",
                help="JSON array of verification criteria.",
            ),
        ] = None,
        milestone: Annotated[Optional[str], typer.Option(help="Milestone ID.")] = None,
        session_id: Annotated[Optional[str], typer.Option(help="Session ID.")] = None,
        json_: Annotated[
            bool, typer.Option("--json", "-J", help="JSON output.")
        ] = False,
    ) -> None:
        """Create a new plan."""
        from ._app import emit

        result = _plan.plan_create(
            project_id=project_id,
            title=title,
            content=content,
            tags=parse_str_list(tags, "--tags"),
            verification=parse_str_list(verification, "--verification"),
            milestone=milestone,
            session_id=session_id,
        )
        emit(result, json_mode=json_)

    @app.command("plan-list")
    def cmd_plan_list(
        project_id: Annotated[str, typer.Option(help="Project GUID.")],
        status: Annotated[Optional[str], typer.Option(help="Filter by status.")] = None,
        json_: Annotated[
            bool, typer.Option("--json", "-J", help="JSON output.")
        ] = False,
    ) -> None:
        """List plans."""
        from ._app import emit

        result = _plan.plan_list(project_id=project_id, status=status)
        emit(result, json_mode=json_)

    @app.command("plan-view")
    def cmd_plan_view(
        project_id: Annotated[str, typer.Option(help="Project GUID.")],
        plan_id: Annotated[str, typer.Argument(help="Plan ID.")],
        json_: Annotated[
            bool, typer.Option("--json", "-J", help="JSON output.")
        ] = False,
    ) -> None:
        """View a plan in full detail."""
        from ._app import emit

        result = _plan.plan_view(project_id=project_id, plan_id=plan_id)
        emit(result, json_mode=json_)

    @app.command("plan-update")
    def cmd_plan_update(
        project_id: Annotated[str, typer.Option(help="Project GUID.")],
        plan_id: Annotated[str, typer.Argument(help="Plan ID.")],
        status: Annotated[Optional[str], typer.Option(help="New status.")] = None,
        title: Annotated[Optional[str], typer.Option(help="New title.")] = None,
        content: Annotated[Optional[str], typer.Option(help="Replace content.")] = None,
        tags: Annotated[
            Optional[str], typer.Option("--tags", help="JSON array of tags.")
        ] = None,
        verification: Annotated[
            Optional[str],
            typer.Option(
                "--verification",
                help="JSON array of verification criteria.",
            ),
        ] = None,
        milestone: Annotated[Optional[str], typer.Option(help="Milestone ID.")] = None,
        append_content: Annotated[
            Optional[str], typer.Option(help="Append to content.")
        ] = None,
        json_: Annotated[
            bool, typer.Option("--json", "-J", help="JSON output.")
        ] = False,
    ) -> None:
        """Update a plan's fields."""
        from ._app import emit

        result = _plan.plan_update(
            project_id=project_id,
            plan_id=plan_id,
            status=status,
            title=title,
            content=content,
            tags=parse_str_list(tags, "--tags"),
            verification=parse_str_list(verification, "--verification"),
            milestone=milestone,
            append_content=append_content,
        )
        emit(result, json_mode=json_)

    @app.command("plan-verify")
    def cmd_plan_verify(
        project_id: Annotated[str, typer.Option(help="Project GUID.")],
        plan_id: Annotated[str, typer.Argument(help="Plan ID.")],
        json_: Annotated[
            bool, typer.Option("--json", "-J", help="JSON output.")
        ] = False,
    ) -> None:
        """Return a plan's verification criteria as a checklist."""
        from ._app import emit

        result = _plan.plan_verify(project_id=project_id, plan_id=plan_id)
        emit(result, json_mode=json_)
