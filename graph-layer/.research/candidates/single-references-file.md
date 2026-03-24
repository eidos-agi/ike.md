---
title: Single REFERENCES.yaml per project
verdict: provisional
---

## What It Is

Add a single .ike/references.yaml file per project that lists connected entities as a flat list. Simplest possible solution. Pro: one file, trivial to implement. Con: loses relationship types between entities (WHO is connected HOW), merge conflicts when multiple agents update the same file, can't traverse from one reference to another. Solves ~40% of the context problem but misses the traversal value that makes graphs useful.

## Validation Checklist

- [ ] Claim 1: N — Gemini confirmed: flat list loses relationship types between references. Cannot traverse from one entity to another. Merge conflicts on shared file. Solves ~40% of context problem at best.

## Scoring
## Scores

| Criterion | Score |
|-----------|-------|
| Git-friendliness | 2/10 |
| LLM traversability | 2/10 |
| Implementation simplicity | 5/10 |
| Human readability | 4/10 |
| Operational overhead | 5/10 |
| **Total** | **18** |

**Notes:** Single file = merge conflicts. No traversal. Trivial to build but solves only ~40% of the problem.
