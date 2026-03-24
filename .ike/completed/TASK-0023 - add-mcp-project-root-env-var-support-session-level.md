---
id: TASK-0023
title: >-
  Add MCP_PROJECT_ROOT env var support — session-level anchor for all trilogy
  tools
status: Done
created: '2026-03-21'
priority: high
tags:
  - trilogy
  - architecture
  - dx
acceptance-criteria:
  - All three servers read MCP_PROJECT_ROOT on startup
  - 'If set, auto-registers as default project without requiring project_set'
  - 'If not set, upward discovery still works'
  - Documented in CONVENTIONS.md and each README
updated: '2026-03-21'
---
All three trilogy MCP servers should read MCP_PROJECT_ROOT at startup. If set, use it as the default project root (eliminating the need to call project_set for the primary project). If not set, fall back to upward discovery from cwd. This makes the session boot protocol clean: set MCP_PROJECT_ROOT in .mcp.json env block or shell, and the trilogy self-configures. Prevents stranded content bugs across sessions.

**Completion notes:** server.ts checks MCP_PROJECT_ROOT env var first. cockpit-eidos .mcp.json now passes MCP_PROJECT_ROOT=/Users/dshanklinbv/repos-eidos-agi/cockpit-eidos.
