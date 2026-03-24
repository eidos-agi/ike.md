---
locked: true
locked_date: '2026-03-23'
---

# Decision Criteria

| # | Criterion | Weight | Description |
|---|-----------|--------|-------------|
| 1 | Git-friendliness | 25 | Clean diffs, low merge conflict probability, works with standard git workflows |
| 2 | LLM traversability | 25 | An agent can read a node, follow edges, and load full project context without human guidance |
| 3 | Implementation simplicity | 20 | Minimal code changes to ike.md, follows existing patterns, shippable in one session |
| 4 | Human readability | 15 | A human can open any file and understand the graph without tooling |
| 5 | Operational overhead | 15 | No external services, no database servers, no maintenance burden |
