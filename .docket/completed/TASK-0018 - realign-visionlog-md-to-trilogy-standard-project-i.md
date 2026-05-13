---
id: TASK-0018
title: >-
  Realign visionlog.md to trilogy standard — project_init/project_set +
  .visionlog/
status: Done
created: '2026-03-21'
priority: high
tags:
  - trilogy
  - standards
  - visionlog
dependencies:
  - TASK-0016
  - TASK-0017
acceptance-criteria:
  - project_init and project_set tools exist with same semantics as ike.md
  - Directory is .visionlog/ by default
  - Config at .visionlog/config.yaml
  - Migration path documented for existing visionlog/ dirs
  - README updated
updated: '2026-03-21'
---
visionlog.md deviates from the trilogy standard on two fronts: (1) tool naming — uses visionlog_register instead of project_init/project_set, (2) directory — uses visible visionlog/ instead of .visionlog/. Realign to match ike.md as the reference implementation: rename tools to project_init + project_set, migrate directory to .visionlog/, update config path to .visionlog/config.yaml. Migration path needed for existing projects (visionlog/ → .visionlog/ rename).

**Completion notes:** Done. visionlog_register → project_set, visionlog_init → project_init, VISIONLOG_DIR changed from 'visionlog' to '.visionlog', all projectIdParam descriptions updated, registry error messages updated, failing test updated. Both builds pass.
