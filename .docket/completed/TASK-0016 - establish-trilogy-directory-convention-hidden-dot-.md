---
id: TASK-0016
title: >-
  Establish trilogy directory convention — hidden dot-dirs, configurable root,
  monorepo docs
status: Done
created: '2026-03-21'
priority: high
tags:
  - distribution
  - trilogy
  - standards
dependencies:
  - TASK-0014
  - TASK-0015
acceptance-criteria:
  - Convention doc written (or section added to each README)
  - All three tools default to hidden dot-dirs
  - Path override documented for monorepo use case
  - 'ike.md, visionlog.md, research.md READMEs consistent'
updated: '2026-03-21'
---
Codify the trilogy's directory convention: all three tools default to dot-dirs at project root (.ike/, .visionlog/, .research/). The dot-prefix is a naming convention only — it signals "tool metadata, not primary source code." These directories are committed to git by default; ignoring them defeats the purpose (task history, decisions, research findings must persist across sessions and contributors). Users may gitignore them only in deliberate local-only workflows. Monorepos are supported by pointing each sub-package's tool init at the sub-package root — each gets its own independent trilogy state. Write a shared convention doc and update all three READMEs.

**Completion notes:** Written as CONVENTIONS.md at repo root. Covers: dot-dir convention, git commitment default, monorepo pattern, GUID routing standard (project_init/project_set/project_id), config file format, and what this is not.
