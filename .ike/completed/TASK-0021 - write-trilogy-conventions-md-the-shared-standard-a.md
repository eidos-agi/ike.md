---
id: TASK-0021
title: Write trilogy CONVENTIONS.md — the shared standard all three tools implement
status: Done
created: '2026-03-21'
priority: medium
tags:
  - trilogy
  - standards
  - docs
dependencies:
  - TASK-0018
  - TASK-0019
acceptance-criteria:
  - CONVENTIONS.md exists in at least one canonical location
  - 'Covers directory, git, GUID routing, tool naming, monorepo patterns'
  - All three READMEs reference it
updated: '2026-03-21'
---
Once TASK-0018 and TASK-0019 are done, the standard exists in three READMEs but not as a single canonical reference. Write CONVENTIONS.md (or a section in each README that links to a shared doc) covering: dot-dir convention, committed by default, monorepo override pattern, project_init/project_set API contract, project_id GUID semantics, error message standards. This is the document future trilogy tools (and contributors) implement against.

**Completion notes:** Done. visionlog.md had no README — created one covering conventions, session protocol, project structure, and full tool list. research.md README updated: .research/ directory structure, project_init rename, trilogy conventions section added with link to CONVENTIONS.md.
