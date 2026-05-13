---
id: TASK-0027
title: Add blocked_reason field to ike.md task schema
status: To Do
created: '2026-03-21'
priority: medium
dependencies:
  - TASK-0026
acceptance-criteria:
  - blocked_reason field in TaskFrontmatter (optional string)
  - task_edit accepts blocked_reason
  - task_view shows blocked_reason when present
  - tests passing
  - binary rebuilt
---
When a task is blocked, agents have nowhere to record why. The escalation SOP branches on reason type: dependency, info gap, contradiction, resource constraint. Without a structured field, the reason lives in conversation and dies there. Add optional blocked_reason to TaskFrontmatter, task_edit schema, and task_view output. Rebuild and test.
