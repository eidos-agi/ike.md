---
id: '0010'
title: 'Convention inheritance: cockpit defines defaults, projects can override'
status: open
evidence: CONFIRMED
sources: 1
created: '2026-03-23'
---

## Claim

Conventions cascade from two levels: cockpit (.ike/conventions.yaml at the cockpit root) and project (.ike/conventions.yaml in the project folder). Projects inherit their cockpit's conventions automatically. A project can override by adding its own conventions.yaml — closest wins, like git config. No separate "org" level needed: the cockpit that spans the org IS the org level. Ike resolves by walking up from project to cockpit. This keeps convention scope tied to the directory structure — no external registry, no config server, just files in the right place.

## Supporting Evidence

> **Evidence: [CONFIRMED]** — Daniel Shanklin design session, 2026-03-23. 'All projects within this cockpit inherit this overloaded convention.', retrieved 2026-03-23

## Caveats

None identified yet.
