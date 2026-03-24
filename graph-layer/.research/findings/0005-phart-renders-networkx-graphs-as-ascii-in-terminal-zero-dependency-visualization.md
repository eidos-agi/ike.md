---
id: '0005'
title: PHART renders NetworkX graphs as ASCII in terminal — zero-dependency visualization
status: open
evidence: CONFIRMED
sources: 1
created: '2026-03-23'
---

## Claim

PHART (Python Hierarchical ASCII Rendering Tool) is pure Python, depends only on NetworkX, renders directed graphs as ASCII/Unicode to stdout. Reads DOT and GraphML. Can be integrated as a graph_render tool in ike to show project context graphs directly in Claude Code terminal. Flow: YAML nodes → NetworkX DiGraph → PHART ASCII output. At 200-500 nodes, rendering is instant.

## Supporting Evidence

> **Evidence: [CONFIRMED]** — PAL research on PHART library; PyPI documentation; comparison with ascii-dag and Cosmo, retrieved 2026-03-23

## Caveats

None identified yet.
