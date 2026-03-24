---
id: 0009
title: Project conventions are cockpit-level, not ike-level — dependency injection
  pattern
status: open
evidence: CONFIRMED
sources: 1
created: '2026-03-23'
---

## Claim

Ike should support cockpit-defined project conventions (via a project-dod.yaml or similar) but never hardcode specific integrations. The AIC convention that every project needs a parent Wrike card is a dependency injection: the cockpit tells ike 'my projects need an external_parent edge of type wrike_card.' Another cockpit could inject jira_ticket or nothing at all. Ike provides: (1) a convention definition file scoped to the cockpit, (2) a project_health tool that validates projects against those conventions. Ike does NOT provide: any knowledge of Wrike, Jira, or any specific external system. The bridge skill (/wrike-work, /jira-work, etc.) handles the actual integration. This keeps ike generic and reusable across organizations while letting each cockpit enforce its own rules.

## Supporting Evidence

> **Evidence: [CONFIRMED]** — Daniel Shanklin design session, 2026-03-23. Key quote: 'it's essentially a dependency injection that we want wrike to own the parent' and 'not every ike project would have an external parent — this is a custom convention.', retrieved 2026-03-23

## Caveats

None identified yet.
