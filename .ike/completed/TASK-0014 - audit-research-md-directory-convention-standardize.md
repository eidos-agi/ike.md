---
id: TASK-0014
title: Audit research.md directory convention — standardize to .research/
status: Done
created: '2026-03-21'
priority: medium
tags:
  - trilogy
  - consistency
  - research
acceptance-criteria:
  - Convention decision recorded as ADR
  - 'If changed: migration path defined'
  - README updated to reflect actual directory structure
updated: '2026-03-21'
---
research.md currently drops research-md.json flat at the project root with no subdirectory. ike.md uses .ike/, visionlog uses visionlog/. The trilogy should have a consistent convention. Evaluate whether research.md should use .research/ to match the hidden-dir pattern of ike.

**Completion notes:** research.md standardized to .research/ dir convention.
