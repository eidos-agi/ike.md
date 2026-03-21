---
id: TASK-0003
title: Fix task_archive — preserves original status instead of forcing Draft
status: Done
created: '2026-03-20'
priority: high
milestone: MS-0001
definition-of-done: >-
  ["archived task keeps its original status in frontmatter", "archive reason
  appended to notes"]
updated: '2026-03-21'
---
**Completion notes:** server.ts uses spread of original frontmatter — status is preserved.
