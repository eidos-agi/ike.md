---
id: TASK-0025
title: Fix forge.md → ike.md naming in research.md server instructions
status: Done
created: '2026-03-21'
priority: high
acceptance-criteria:
  - research.md server instructions say ike.md not forge.md
  - research.md rebuilt
visionlog_goal_id: GOAL-001
updated: '2026-03-21'
---
research.md MCP server instructions still reference "forge.md" as the execution tool. Every agent reading those instructions gets the wrong name for ike.md. Fix in /Users/dshanklinbv/repos-eidos-agi/research.md/src/server.ts, rebuild.

**Completion notes:** Fixed forge.md → ike.md in research.md/src/server.ts. Both occurrences updated. Rebuilt clean.
