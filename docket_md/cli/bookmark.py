"""Bookmark subcommand."""

from __future__ import annotations

from typing import Annotated

import typer

from .._logic import bookmark as _bookmark


def register(app: typer.Typer) -> None:
    @app.command("bookmark")
    def cmd_bookmark(
        project_id: Annotated[str, typer.Option(help="Project GUID.")],
        note: Annotated[str, typer.Option(help="Bookmark note.")],
        json_: Annotated[
            bool, typer.Option("--json", "-J", help="JSON output.")
        ] = False,
    ) -> None:
        """Bookmark the current state with a note."""
        from ._app import emit

        result = _bookmark.bookmark(project_id=project_id, note=note)
        emit(result, json_mode=json_)
