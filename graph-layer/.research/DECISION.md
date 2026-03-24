# Decision

**Date:** 2026-03-23
**Status:** Decided

## Decision

Add .ike/graph/ with YAML node files and four new tools (graph_create_node, graph_get_node, graph_add_edge, graph_list_nodes) directly inside ike.md. No separate service. No recursive projects — use subproject edges. Optional graph_render via PHART for ASCII visualization.

## Rationale

Scored 24/25 vs 18 and 15 for alternatives. Six confirmed findings support this approach: (1) file-based micrographs are the industry standard at this scale, (2) graph belongs inside ike for project-scoped context, (3) flat projects with edge-based hierarchy beat recursive directories, (4) typed edges between nodes beat a flat references list, (5) PHART enables zero-dependency terminal visualization, (6) GraphRAG is complementary, not a replacement. Peer-reviewed by Gemini 2.5 Pro with full source code access — unanimous recommendation. Implementation estimated at ~150 lines following existing ike patterns across config.py, files.py, and server.py.
