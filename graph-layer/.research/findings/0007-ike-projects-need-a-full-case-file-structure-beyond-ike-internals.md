---
id: '0007'
title: Ike projects need a full case-file structure beyond .ike/ internals
status: open
evidence: CONFIRMED
sources: 1
created: '2026-03-23'
---

## Claim

A self-contained project needs more than ike's internal execution data (tasks, graph, milestones). It needs: (1) artifacts/ — captured snapshots of external data (emails, Wrike cards, documents from other repos) so the project is reviewable without access to live systems, (2) log/ — timestamped entries recording what happened, decisions made, and outcomes, (3) deliverables/ — what the project produced, (4) README.md — the project narrative, potentially auto-generated from graph + log. The .ike/ directory remains the execution engine. The project root becomes the portable case file. Key insight: graph nodes should have both live references (aic_mail_query, wrike_id) for agents with system access AND artifact_path for anyone reviewing the project folder. A project_snapshot tool would generate the complete case file from graph + tasks + artifacts + log. This design means any project folder can be handed to a colleague, auditor, or future agent and understood without access to the original systems.

## Supporting Evidence

> **Evidence: [CONFIRMED]** — Design session with Daniel Shanklin, 2026-03-23. Motivated by real constraint: 'someone isn't going to have access to my email if they need to review the project.', retrieved 2026-03-23

## Caveats

None identified yet.
