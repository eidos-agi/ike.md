"""Graph subcommands."""

from __future__ import annotations

from typing import Annotated, Optional

import typer

from .._logic import graph as _graph
from ._helpers import parse_dict, parse_list_of_dicts


def register(app: typer.Typer) -> None:
    @app.command("graph-create-node")
    def cmd_graph_create_node(
        project_id: Annotated[str, typer.Option(help="Project GUID.")],
        node_id: Annotated[str, typer.Option(help="Unique node ID.")],
        node_type: Annotated[str, typer.Option(help="Node type.")],
        title: Annotated[str, typer.Option(help="Human-readable title.")],
        attributes: Annotated[
            Optional[str],
            typer.Option("--attributes", help="JSON object of attributes."),
        ] = None,
        edges: Annotated[
            Optional[str],
            typer.Option(
                "--edges",
                help='JSON array of edges, e.g. [{"type":"...","target":"..."}].',
            ),
        ] = None,
        json_: Annotated[
            bool, typer.Option("--json", "-J", help="JSON output.")
        ] = False,
    ) -> None:
        """Create a graph node."""
        from ._app import emit

        result = _graph.graph_create_node(
            project_id=project_id,
            node_id=node_id,
            node_type=node_type,
            title=title,
            attributes=parse_dict(attributes, "--attributes"),
            edges=parse_list_of_dicts(edges, "--edges"),
        )
        emit(result, json_mode=json_)

    @app.command("graph-get-node")
    def cmd_graph_get_node(
        project_id: Annotated[str, typer.Option(help="Project GUID.")],
        node_id: Annotated[str, typer.Argument(help="Node ID.")],
        json_: Annotated[
            bool, typer.Option("--json", "-J", help="JSON output.")
        ] = False,
    ) -> None:
        """Read a graph node."""
        from ._app import emit

        result = _graph.graph_get_node(project_id=project_id, node_id=node_id)
        emit(result, json_mode=json_)

    @app.command("graph-add-edge")
    def cmd_graph_add_edge(
        project_id: Annotated[str, typer.Option(help="Project GUID.")],
        source_node_id: Annotated[str, typer.Option(help="Source node ID.")],
        edge_type: Annotated[str, typer.Option(help="Edge type.")],
        target_node_id: Annotated[str, typer.Option(help="Target node ID.")],
        json_: Annotated[
            bool, typer.Option("--json", "-J", help="JSON output.")
        ] = False,
    ) -> None:
        """Add a typed edge from one node to another."""
        from ._app import emit

        result = _graph.graph_add_edge(
            project_id=project_id,
            source_node_id=source_node_id,
            edge_type=edge_type,
            target_node_id=target_node_id,
        )
        emit(result, json_mode=json_)

    @app.command("graph-list-nodes")
    def cmd_graph_list_nodes(
        project_id: Annotated[str, typer.Option(help="Project GUID.")],
        node_type: Annotated[
            Optional[str], typer.Option(help="Filter by node type.")
        ] = None,
        query: Annotated[Optional[str], typer.Option(help="Filter by keyword.")] = None,
        json_: Annotated[
            bool, typer.Option("--json", "-J", help="JSON output.")
        ] = False,
    ) -> None:
        """List graph nodes with optional filtering."""
        from ._app import emit

        result = _graph.graph_list_nodes(
            project_id=project_id, node_type=node_type, query=query
        )
        emit(result, json_mode=json_)

    @app.command("graph-traverse")
    def cmd_graph_traverse(
        project_id: Annotated[str, typer.Option(help="Project GUID.")],
        node_id: Annotated[str, typer.Argument(help="Starting node ID.")],
        depth: Annotated[int, typer.Option(help="How many hops to follow.")] = 1,
        json_: Annotated[
            bool, typer.Option("--json", "-J", help="JSON output.")
        ] = False,
    ) -> None:
        """Follow edges from a node and return the connected subgraph."""
        from ._app import emit

        result = _graph.graph_traverse(
            project_id=project_id, node_id=node_id, depth=depth
        )
        emit(result, json_mode=json_)
