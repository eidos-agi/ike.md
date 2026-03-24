---
title: Add .ike/graph/ with YAML node files and four new tools
verdict: provisional
---

## What It Is

Extend ike.md with a .ike/graph/ directory. One YAML file per node (typed: person, email, wrike_card, artifact, deadline, project). Each node has attributes and typed edges to other nodes. Four new tools: graph_create_node, graph_get_node, graph_add_edge, graph_list_nodes. Optional graph_render using PHART for ASCII visualization. No recursive projects — use subproject edges. Follows existing ike patterns (config.py DIRECTORIES, files.py helpers, server.py tools). Estimated: ~150 lines of new code across 3 files.

## Validation Checklist

- [ ] Claim 1: Y — Validated by Gemini 2.5 Pro architectural review: graph inside ike is correct for project-scoped context. Confirmed by examining ike source code — existing patterns for tasks/milestones/documents directly extend to graph nodes. ~150 lines estimated.

## Scoring
## Scores

| Criterion | Score |
|-----------|-------|
| Git-friendliness | 5/10 |
| LLM traversability | 5/10 |
| Implementation simplicity | 4/10 |
| Human readability | 5/10 |
| Operational overhead | 5/10 |
| **Total** | **24** |

**Notes:** One YAML file per node = excellent git diffs, no merge conflicts between nodes. Agent reads YAML natively, follows edges by ID. ~150 lines following existing ike patterns. Any human can read a .yaml file. Zero external dependencies.
