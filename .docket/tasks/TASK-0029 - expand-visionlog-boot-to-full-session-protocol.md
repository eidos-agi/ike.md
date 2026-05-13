---
id: TASK-0029
title: Expand visionlog_boot to full session protocol
status: To Do
created: '2026-03-21'
priority: medium
dependencies:
  - TASK-0026
  - TASK-0028
acceptance-criteria:
  - visionlog_boot output includes open question count
  - >-
    visionlog_boot surfaces goals that have no linked ike tasks (needs
    decomposition)
  - visionlog_boot includes next-action guidance referencing SOPs
  - tests passing
  - binary rebuilt
---
visionlog_boot currently shows goals and guardrails. It should orient the agent fully: active goals with their ike task counts, open questions, research.md projects in flight, and the decomposition SOP if any goals have no tasks yet. Boot should tell the agent exactly what to call next, not just what the project contains.
