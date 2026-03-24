---
id: '0003'
title: Recursive projects are overengineered — use graph edges instead
status: open
evidence: CONFIRMED
sources: 1
created: '2026-03-23'
---

## Claim

Flat projects linked by typed edges (e.g., type: subproject) are superior to physically nested .ike/ directories. Graph edges are more flexible (support any relationship type), simpler to query, and avoid locking logical hierarchy into physical directory structure. Cross-hierarchy queries become trivial graph traversals instead of recursive filesystem walks.

## Supporting Evidence

> **Evidence: [CONFIRMED]** — Gemini 2.5 Pro architectural review — explicit recommendation against recursive projects, retrieved 2026-03-23

## Caveats

None identified yet.
