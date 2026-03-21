---
id: TASK-0019
title: >-
  Realign research.md to trilogy standard — project_init/project_set +
  .research/
status: Done
created: '2026-03-21'
priority: high
tags:
  - trilogy
  - standards
  - research
dependencies:
  - TASK-0016
  - TASK-0017
acceptance-criteria:
  - project_init and project_set tools exist with same semantics as ike.md
  - Directory is .research/ by default
  - Config at .research/research.json
  - Migration path documented for existing research-md.json files
  - README updated
updated: '2026-03-21'
---
research.md deviates from the trilogy standard: (1) drops a flat research-md.json at project root with no subdirectory, (2) tool naming for registration is inconsistent with project_init/project_set pattern. Realign: create .research/ directory, move config to .research/research.json, expose project_init and project_set tools matching ike.md semantics. Migration path for existing research-md.json files needed.

**Completion notes:** Done. CONFIG_DIR='.research', CONFIG_FILENAME='research.json'. loadConfig/saveConfig use dir/.research/research.json. initProject creates .research/findings/, .research/candidates/, .research/evaluations/. server.ts: 'init' tool → 'project_init', descriptions updated. Both builds pass.
