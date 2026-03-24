---
id: TASK-0022
title: Eliminate CWD-based default core fallback — fail loudly if no project context
status: Done
created: '2026-03-21'
priority: high
tags:
  - trilogy
  - architecture
  - safety
acceptance-criteria:
  - Write tools throw immediately if no project_id and no auto-detected root
  - 'Error message tells agent exactly how to fix: call project_set first'
  - Read-only tools may still auto-detect from upward walk
  - No silent routing to process CWD
updated: '2026-03-21'
---
visionlog's defaultCore (and research.md's analogous fallback) silently routes writes to the MCP server's process CWD when no project_id is set. This caused content from multiple projects to accumulate in /Users/dshanklinbv/visionlog/. The fix: remove CWD-based defaults entirely. Any write tool called without a valid registered project_id should throw ProjectContextNotSetError with an instructional message. Read-only tools (status, list) may still work against the auto-detected root as a convenience, but writes must never silently route.

**Completion notes:** registry.resolve() now checks for .visionlog/config.yaml before returning defaultCore. Throws clear error with instructions if not initialized.
