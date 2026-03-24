---
id: TASK-0024
title: >-
  Migrate stranded /Users/dshanklinbv/visionlog/ content to correct project
  visionlogs
status: Done
created: '2026-03-21'
priority: medium
tags:
  - trilogy
  - cleanup
  - migration
acceptance-criteria:
  - ike.md vision + goals + guardrails migrated to ike.md .visionlog/
  - resume-resume content migrated to resume-resume repo .visionlog/
  - /Users/dshanklinbv/visionlog/ deleted
  - /Users/dshanklinbv/.visionlog/ deleted
  - No more home-dir visionlog catch-all
updated: '2026-03-21'
---
Home-dir /Users/dshanklinbv/visionlog/ contains content from multiple projects routed there by the CWD fallback bug. Content inventory: ike.md vision + GOAL-012/013 + GUARD-002 (belong in ike.md .visionlog/), resume-resume GUARD-001 + ADR-001 (belong in resume-resume repo). /Users/dshanklinbv/.visionlog/ is empty except config (from a stale project_init call) — safe to delete. After migration, delete both stale dirs to prevent future accidental routing.

**Completion notes:** All stranded content from ~/visionlog/ migrated to correct project visionlogs. depends_on DAG links wired. Stale home dirs deleted.
