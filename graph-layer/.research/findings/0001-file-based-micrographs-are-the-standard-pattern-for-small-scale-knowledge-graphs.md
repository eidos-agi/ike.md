---
id: '0001'
title: File-based micrographs are the standard pattern for small-scale knowledge graphs
status: open
evidence: CONFIRMED
sources: 1
created: '2026-03-23'
---

## Claim

For graphs under ~1,000 nodes with a single user and git-friendly constraints, the industry-recognized pattern is "micrograph in files, in-memory graph at runtime." YAML/JSON node files loaded into NetworkX at query time. This is the same pattern used by yaml2graph, sift-kg, infrastructure-as-code (Ansible, Terraform), and static site generators (Hugo). Graph databases (Neo4j, Dgraph) are recommended only at many thousands of nodes, multi-user, or heavy analytics scenarios. At 200-500 nodes, file-based is not naive — it is the recommended approach.

## Supporting Evidence

> **Evidence: [CONFIRMED]** — Gemini 2.5 Pro architectural review (two rounds); PAL research on micrograph patterns, yaml2graph, sift-kg, NetworkX vs Neo4j comparisons, retrieved 2026-03-23

## Caveats

None identified yet.
