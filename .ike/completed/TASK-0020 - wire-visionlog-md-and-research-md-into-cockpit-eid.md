---
id: TASK-0020
title: Wire visionlog.md and research.md into cockpit-eidos .mcp.json
status: Done
created: '2026-03-21'
priority: high
tags:
  - trilogy
  - standards
  - dx
dependencies:
  - TASK-0018
  - TASK-0019
acceptance-criteria:
  - visionlog entry added to .mcp.json
  - research.md entry added to .mcp.json
  - Both servers confirmed working in a cockpit-eidos session
  - mcp__visionlog__ and mcp__research__ tools available
updated: '2026-03-21'
---
cockpit-eidos .mcp.json has ike but not visionlog or research.md. Without all three wired, the trilogy loop cannot run autonomously from within cockpit-eidos sessions — research.md decisions can't be made via tool, and visionlog ADRs can't be written via tool. Add both servers. Depends on their dist/ being built and paths confirmed.

**Completion notes:** Done. visionlog (dist/visionlog binary, mcp start) and research-md (node bin/research-md.js mcp start) added to cockpit-eidos .mcp.json. Both added to _registry_managed. Full trilogy now wired.
