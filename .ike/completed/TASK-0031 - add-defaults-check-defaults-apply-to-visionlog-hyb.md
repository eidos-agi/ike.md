---
id: TASK-0031
title: Add defaults-check / defaults-apply to visionlog (hybrid pull model)
status: Done
created: '2026-03-21'
priority: medium
tags:
  - trilogy
  - visionlog
  - defaults
  - governance
acceptance-criteria:
  - >-
    defaults.json exists in visionlog.md repo root with schemaVersion field and
    sops array
  - >-
    visionlog_defaults_check tool fetches remote, compares against bundled and
    local, returns structured diff
  - visionlog_defaults_apply tool applies user-selected items after review
  - project_init continues to work fully offline using bundled defaults
  - >-
    Schema version mismatch produces a clear error directing user to update the
    package
  - >-
    Signature verification implemented or scaffolded with clear TODO for key
    generation
updated: '2026-03-21'
---
Implement a pull-based defaults update mechanism for visionlog. Users should be able to retrieve updated default SOPs from upstream without requiring a package update. Uses a hybrid model: bundled defaults for offline-safe init, remote fetch for governance content updates.

Architecture:
- `defaults.json` in repo root (schemaVersion, sops array)
- `defaults.json.sig` for cryptographic integrity verification
- Public key bundled in package
- `visionlog_defaults_check` MCP tool: fetch remote + three-way diff (local vs bundled vs remote)
- `visionlog_defaults_apply` MCP tool: apply selected items after explicit user review

Key principles:
- Fetch ≠ Apply — deliberate consent required (governance-consistent)
- Offline-first: project_init never depends on network
- Schema version field for forward-compat signaling
- Signature verification blocks apply if integrity check fails

**Completion notes:** Implemented hybrid pull model. defaults.json live at eidos-agi/visionlog.md main. defaults_check + defaults_apply tools registered. Private repo handled via VISIONLOG_GITHUB_TOKEN env → GitHub API fallback. Full proof suite: drift detection, idempotency, schema mismatch guard, customization warning, new SOP detection, unknown title error, double-init no-dup, live remote fetch verified.
