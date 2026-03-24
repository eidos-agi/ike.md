---
id: TASK-0030
title: Seed trilogy operational SOPs into visionlog project_init defaults
status: Done
created: '2026-03-21'
priority: high
dependencies:
  - TASK-0026
acceptance-criteria:
  - project_init creates SOP-001 Goal Decomposition by default
  - project_init creates SOP-002 Completion Feedback by default
  - project_init creates SOP-003 Blocked Task Escalation by default
  - existing projects can opt-in via a new backfill command
  - tests cover default SOP seeding
  - binary rebuilt
visionlog_goal_id: GOAL-001
updated: '2026-03-21'
---
Goal Decomposition, Completion Feedback, and Blocked Task Escalation are universal trilogy SOPs — they apply to every project, not just cockpit-eidos. Currently they only exist in cockpit-eidos visionlog. project_init should seed them automatically so every new visionlog project starts with the trilogy operating manual. These are meta-SOPs: they govern how the trilogy is used, not what the project does.

**Completion notes:** seedDefaultSops() added to VisionCore.init(). Idempotent — skips if SOPs already exist. All three trilogy SOPs seeded on every project_init. 75/75 tests passing.
