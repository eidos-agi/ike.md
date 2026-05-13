---
id: TASK-0017
title: Align GUID routing tool names across the trilogy (project_set / project_init)
status: Done
created: '2026-03-21'
priority: high
tags:
  - distribution
  - trilogy
  - dx
dependencies:
  - TASK-0016
acceptance-criteria:
  - >-
    Tool names consistent across all three (register, set, or init pattern
    chosen)
  - All three READMEs document the same pattern
  - Error messages use consistent language
updated: '2026-03-21'
---
Each tool has GUID routing but with different tool names. ike.md uses project_set/project_init. visionlog.md uses visionlog_register. research.md has GUID routing but tool naming unclear. An agent working across all three has to remember three different APIs. Standardize to a consistent pattern: either {tool}_set/{tool}_init or project_set/project_init with tool-scoped namespacing. Decision should be documented in visionlog before implementation.

**Completion notes:** Resolved by CONVENTIONS.md: standard is project_init + project_set, parameter is project_id. Implemented in TASK-0018 and TASK-0019.
