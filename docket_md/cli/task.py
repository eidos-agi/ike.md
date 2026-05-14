"""Task subcommands."""

from __future__ import annotations

from typing import Annotated, Optional

import typer

from .._logic import task as _task
from ._helpers import parse_str_list


def register(app: typer.Typer) -> None:
    @app.command("task-create")
    def cmd_task_create(
        project_id: Annotated[str, typer.Option(help="Project GUID.")],
        title: Annotated[str, typer.Option(help="Task title.")],
        description: Annotated[str, typer.Option(help="Description.")] = "",
        status: Annotated[
            str, typer.Option(help="To Do | In Progress | Done.")
        ] = "To Do",
        priority: Annotated[Optional[str], typer.Option(help="Priority.")] = None,
        milestone: Annotated[Optional[str], typer.Option(help="Milestone ID.")] = None,
        assignees: Annotated[
            Optional[str],
            typer.Option("--assignees", help="JSON array of assignees."),
        ] = None,
        tags: Annotated[
            Optional[str],
            typer.Option("--tags", help="JSON array of tags."),
        ] = None,
        dependencies: Annotated[
            Optional[str],
            typer.Option("--dependencies", help="JSON array of task IDs."),
        ] = None,
        acceptance_criteria: Annotated[
            Optional[str],
            typer.Option("--acceptance-criteria", help="JSON array of criteria."),
        ] = None,
        definition_of_done: Annotated[
            Optional[str],
            typer.Option("--definition-of-done", help="JSON array of DoD items."),
        ] = None,
        visionlog_goal_id: Annotated[
            Optional[str], typer.Option(help="Linked visionlog goal ID.")
        ] = None,
        blocked_reason: Annotated[
            Optional[str], typer.Option(help="Blocker description.")
        ] = None,
        json_: Annotated[
            bool, typer.Option("--json", "-J", help="JSON output.")
        ] = False,
    ) -> None:
        """Create a new task."""
        from ._app import emit

        result = _task.task_create(
            project_id=project_id,
            title=title,
            description=description,
            status=status,
            priority=priority,
            milestone=milestone,
            assignees=parse_str_list(assignees, "--assignees"),
            tags=parse_str_list(tags, "--tags"),
            dependencies=parse_str_list(dependencies, "--dependencies"),
            acceptance_criteria=parse_str_list(
                acceptance_criteria, "--acceptance-criteria"
            ),
            definition_of_done=parse_str_list(
                definition_of_done, "--definition-of-done"
            ),
            visionlog_goal_id=visionlog_goal_id,
            blocked_reason=blocked_reason,
        )
        emit(result, json_mode=json_)

    @app.command("task-list")
    def cmd_task_list(
        project_id: Annotated[str, typer.Option(help="Project GUID.")],
        status: Annotated[Optional[str], typer.Option(help="Filter by status.")] = None,
        milestone: Annotated[
            Optional[str], typer.Option(help="Filter by milestone.")
        ] = None,
        assignee: Annotated[
            Optional[str], typer.Option(help="Filter by assignee.")
        ] = None,
        tag: Annotated[Optional[str], typer.Option(help="Filter by tag.")] = None,
        include_completed: Annotated[
            bool, typer.Option(help="Include completed/.")
        ] = False,
        json_: Annotated[
            bool, typer.Option("--json", "-J", help="JSON output.")
        ] = False,
    ) -> None:
        """List tasks with optional filtering."""
        from ._app import emit

        result = _task.task_list(
            project_id=project_id,
            status=status,
            milestone=milestone,
            assignee=assignee,
            tag=tag,
            include_completed=include_completed,
        )
        emit(result, json_mode=json_)

    @app.command("task-view")
    def cmd_task_view(
        project_id: Annotated[str, typer.Option(help="Project GUID.")],
        task_id: Annotated[str, typer.Argument(help="Task ID.")],
        json_: Annotated[
            bool, typer.Option("--json", "-J", help="JSON output.")
        ] = False,
    ) -> None:
        """View a task in full detail by ID."""
        from ._app import emit

        result = _task.task_view(project_id=project_id, task_id=task_id)
        emit(result, json_mode=json_)

    @app.command("task-edit")
    def cmd_task_edit(
        project_id: Annotated[str, typer.Option(help="Project GUID.")],
        task_id: Annotated[str, typer.Argument(help="Task ID.")],
        title: Annotated[Optional[str], typer.Option(help="New title.")] = None,
        description: Annotated[
            Optional[str], typer.Option(help="Replace description.")
        ] = None,
        status: Annotated[Optional[str], typer.Option(help="New status.")] = None,
        priority: Annotated[Optional[str], typer.Option(help="New priority.")] = None,
        milestone: Annotated[Optional[str], typer.Option(help="New milestone.")] = None,
        assignees: Annotated[
            Optional[str],
            typer.Option("--assignees", help="JSON array of assignees."),
        ] = None,
        tags: Annotated[
            Optional[str], typer.Option("--tags", help="JSON array of tags.")
        ] = None,
        dependencies: Annotated[
            Optional[str],
            typer.Option("--dependencies", help="JSON array of task IDs."),
        ] = None,
        acceptance_criteria: Annotated[
            Optional[str],
            typer.Option("--acceptance-criteria", help="JSON array of criteria."),
        ] = None,
        definition_of_done: Annotated[
            Optional[str],
            typer.Option("--definition-of-done", help="JSON array of DoD items."),
        ] = None,
        blocked_reason: Annotated[
            Optional[str], typer.Option(help='New blocker or "" to clear.')
        ] = None,
        append_notes: Annotated[
            Optional[str], typer.Option(help="Append to existing notes.")
        ] = None,
        json_: Annotated[
            bool, typer.Option("--json", "-J", help="JSON output.")
        ] = False,
    ) -> None:
        """Edit a task's fields."""
        from ._app import emit

        result = _task.task_edit(
            project_id=project_id,
            task_id=task_id,
            title=title,
            description=description,
            status=status,
            priority=priority,
            milestone=milestone,
            assignees=parse_str_list(assignees, "--assignees"),
            tags=parse_str_list(tags, "--tags"),
            dependencies=parse_str_list(dependencies, "--dependencies"),
            acceptance_criteria=parse_str_list(
                acceptance_criteria, "--acceptance-criteria"
            ),
            definition_of_done=parse_str_list(
                definition_of_done, "--definition-of-done"
            ),
            blocked_reason=blocked_reason,
            append_notes=append_notes,
        )
        emit(result, json_mode=json_)

    @app.command("task-complete")
    def cmd_task_complete(
        project_id: Annotated[str, typer.Option(help="Project GUID.")],
        task_id: Annotated[str, typer.Argument(help="Task ID.")],
        notes: Annotated[Optional[str], typer.Option(help="Completion notes.")] = None,
        json_: Annotated[
            bool, typer.Option("--json", "-J", help="JSON output.")
        ] = False,
    ) -> None:
        """Mark a task as Done and move it to completed/."""
        from ._app import emit

        result = _task.task_complete(
            project_id=project_id, task_id=task_id, notes=notes
        )
        emit(result, json_mode=json_)

    @app.command("task-archive")
    def cmd_task_archive(
        project_id: Annotated[str, typer.Option(help="Project GUID.")],
        task_id: Annotated[str, typer.Argument(help="Task ID.")],
        reason: Annotated[Optional[str], typer.Option(help="Archive reason.")] = None,
        json_: Annotated[
            bool, typer.Option("--json", "-J", help="JSON output.")
        ] = False,
    ) -> None:
        """Archive a task."""
        from ._app import emit

        result = _task.task_archive(
            project_id=project_id, task_id=task_id, reason=reason
        )
        emit(result, json_mode=json_)

    @app.command("task-search")
    def cmd_task_search(
        project_id: Annotated[str, typer.Option(help="Project GUID.")],
        query: Annotated[str, typer.Argument(help="Search keyword.")],
        include_completed: Annotated[
            bool, typer.Option(help="Include completed/.")
        ] = False,
        json_: Annotated[
            bool, typer.Option("--json", "-J", help="JSON output.")
        ] = False,
    ) -> None:
        """Search tasks by keyword."""
        from ._app import emit

        result = _task.task_search(
            project_id=project_id,
            query=query,
            include_completed=include_completed,
        )
        emit(result, json_mode=json_)
