---
id: '0004'
title: A single REFERENCES.yaml is insufficient — full graph needed
status: open
evidence: CONFIRMED
sources: 1
created: '2026-03-23'
---

## Claim

A flat references list captures WHAT is related but not HOW. The agent needs to know that Suman is-vendor-on the Wrike card, which is-blocked-by her non-response. Typed edges between individual nodes provide this traversal capability. The node-per-file model is also better for git (fewer merge conflicts) than a single monolithic file. The marginal complexity of a proper graph over a flat list is justified by the traversal value.

## Supporting Evidence

> **Evidence: [CONFIRMED]** — Gemini 2.5 Pro architectural review — direct comparison of REFERENCES.yaml vs node-per-file graph, retrieved 2026-03-23

## Caveats

None identified yet.
