---
title: Separate Marshall MCP server for the graph
verdict: provisional
---

## What It Is

Build a standalone MCP server that owns the graph layer, independent of ike. Would have its own storage (.marshall/ or .graph/), its own GUID system, its own tools. Ike remains task-only. Marshall handles connections. Pro: separation of concerns, could serve multiple ike projects from one graph. Con: two systems to learn, cross-service coordination, split mental model, more operational overhead. Not recommended at current scale.

## Validation Checklist

- [ ] Claim 1: N — Gemini explicitly recommended against: introduces cross-service coordination and split mental model without benefit at this scale. Same storage pattern (YAML files) means no technical advantage over in-ike approach.

## Scoring
## Scores

| Criterion | Score |
|-----------|-------|
| Git-friendliness | 4/10 |
| LLM traversability | 3/10 |
| Implementation simplicity | 2/10 |
| Human readability | 4/10 |
| Operational overhead | 2/10 |
| **Total** | **15** |

**Notes:** Same YAML storage but split across two systems. LLM must coordinate ike + marshall = extra tool calls. New MCP server from scratch. Second process to run and debug.
