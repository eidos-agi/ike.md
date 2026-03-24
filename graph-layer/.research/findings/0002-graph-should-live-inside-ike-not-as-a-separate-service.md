---
id: '0002'
title: Graph should live inside ike, not as a separate service
status: open
evidence: CONFIRMED
sources: 1
created: '2026-03-23'
---

## Claim

The knowledge graph solves project-scoped context. Ike is the project system. Co-locating .ike/graph/ within the project directory keeps the project self-contained and avoids cross-service coordination. A separate "Marshall" MCP would introduce operational overhead and split the mental model without meaningful benefit at this scale. The graph tools follow the same patterns as existing task/milestone/document tools.

## Supporting Evidence

> **Evidence: [CONFIRMED]** — Gemini 2.5 Pro architectural review — direct answer to "inside vs separate service" question, retrieved 2026-03-23

## Caveats

None identified yet.
