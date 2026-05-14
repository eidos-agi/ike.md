"""Document subcommands."""

from __future__ import annotations

from typing import Annotated, Optional

import typer

from .._logic import document as _document
from ._helpers import parse_str_list


def register(app: typer.Typer) -> None:
    @app.command("document-create")
    def cmd_document_create(
        project_id: Annotated[str, typer.Option(help="Project GUID.")],
        title: Annotated[str, typer.Option(help="Document title.")],
        content: Annotated[str, typer.Option(help="Document body.")] = "",
        tags: Annotated[
            Optional[str], typer.Option("--tags", help="JSON array of tags.")
        ] = None,
        json_: Annotated[
            bool, typer.Option("--json", "-J", help="JSON output.")
        ] = False,
    ) -> None:
        """Create a project document."""
        from ._app import emit

        result = _document.document_create(
            project_id=project_id,
            title=title,
            content=content,
            tags=parse_str_list(tags, "--tags"),
        )
        emit(result, json_mode=json_)

    @app.command("document-list")
    def cmd_document_list(
        project_id: Annotated[str, typer.Option(help="Project GUID.")],
        json_: Annotated[
            bool, typer.Option("--json", "-J", help="JSON output.")
        ] = False,
    ) -> None:
        """List all documents."""
        from ._app import emit

        result = _document.document_list(project_id=project_id)
        emit(result, json_mode=json_)

    @app.command("document-view")
    def cmd_document_view(
        project_id: Annotated[str, typer.Option(help="Project GUID.")],
        document_id: Annotated[str, typer.Argument(help="Document ID.")],
        json_: Annotated[
            bool, typer.Option("--json", "-J", help="JSON output.")
        ] = False,
    ) -> None:
        """View a document by ID."""
        from ._app import emit

        result = _document.document_view(project_id=project_id, document_id=document_id)
        emit(result, json_mode=json_)

    @app.command("document-update")
    def cmd_document_update(
        project_id: Annotated[str, typer.Option(help="Project GUID.")],
        document_id: Annotated[str, typer.Argument(help="Document ID.")],
        title: Annotated[Optional[str], typer.Option(help="New title.")] = None,
        content: Annotated[Optional[str], typer.Option(help="Replace content.")] = None,
        tags: Annotated[
            Optional[str], typer.Option("--tags", help="JSON array of tags.")
        ] = None,
        append_content: Annotated[
            Optional[str], typer.Option(help="Append to content.")
        ] = None,
        json_: Annotated[
            bool, typer.Option("--json", "-J", help="JSON output.")
        ] = False,
    ) -> None:
        """Update a document."""
        from ._app import emit

        result = _document.document_update(
            project_id=project_id,
            document_id=document_id,
            title=title,
            content=content,
            tags=parse_str_list(tags, "--tags"),
            append_content=append_content,
        )
        emit(result, json_mode=json_)
