# repo at /Users/dshanklinbv/repos-eidos-agi/ike.md

**Target:** /Users/dshanklinbv/repos-eidos-agi/ike.md
**Type:** repo
**Tested as:** Software Engineer
**Last tested:** 2026-03-21 00:06 UTC
**Status:** FLAKY (50/51 checks passed)
**Rounds:** 5
**Test suite:** `/Users/dshanklinbv/repos-eidos-agi/ike.md/.test-forge/suites/Users-dshanklinbv-repos-eidos-agi-ike.md.yaml`

## What "working" means
imports work, tests pass, repo is clean

## What's working
- **server-starts-and-lists-tools** — passed (131.8ms) — Verifies the MCP server starts, accepts stdin JSON-RPC, and responds with a tools list. If this fails nothing else can pass.
- **tools-list-contains-expected-14-tools** — passed (92.6ms) — Counts and names all registered tools. README says 14 but the MCP system reminder shows 19 — this surfaces the discrepancy and confirms exact tool inventory.
- **project-list-no-args** — passed (92.3ms) — project_list should work with no arguments. Verifies the GUID registry is readable and returns a sensible list (possibly empty on a fresh install).
- **project-init-creates-ike-json** — passed (93.8ms) — Core GUID workflow: project_init should create .ike/ike.json in the given path and return a stable GUID. Tests directory creation, JSON write, and GUID generation.
- **project-set-registers-existing-project** — passed (92.4ms) — After project_init, project_set should re-register the same path and return the same GUID. Tests idempotency of the registry and path→GUID lookup.
- **project-set-unknown-path-error** — passed (92.0ms) — A path with no .ike/ike.json should return an error — and that error message should tell the user to call project_init. Tests the error guidance contract from the README.
- **task-list-without-project-id-error** — passed (90.5ms) — Calling task_list with no project_id should fail gracefully. Verifies the server doesn't crash and returns a useful error (not a stack trace).
- **task-create-full-payload** — passed (91.6ms) — Creates a real task to verify task_create writes correctly and returns a task object with an ID. The returned ID is needed for task_view, task_edit, task_complete, task_archive probes.
- **task-list-returns-created-task** — passed (91.8ms) — After task_create, task_list must return the new task. Tests read-after-write consistency and that list results include the expected fields.
- **task-search-by-keyword** — passed (90.5ms) — Searches for the task we just created. Verifies the search index is updated on create and that keyword matching works against title/description.
- **milestone-create-basic** — passed (89.2ms) — Milestone create is separate from task create — tests that the milestone data model is independent and the create→list→view lifecycle works.
- **milestone-list-shows-created-milestone** — passed (90.0ms) — Read-after-write for milestones. Also checks response shape — each entry should have at minimum an id, title, and status field.
- **document-create-basic** — passed (90.9ms) — Documents are the third entity type. Tests that all three entity types (task / milestone / document) can be created independently without cross-contamination.
- **project-info-returns-metadata** — passed (88.9ms) — project_info should return project name, path, GUID, and creation date. Validates the metadata layer is populated on init and readable by ID.
- **dist-index-js-exists** — passed (6.3ms) — The dist-build-is-fresh failure checked for '1' which is ambiguous. Directly verify the compiled entry point exists.
- **task-view-specific-task** — passed (132.3ms) — task_view was never exercised — verifies individual task retrieval by ID returns correct shape.
- **task-edit-update-title** — passed (88.4ms) — Verifies task mutation works and persists — core CRUD gap not yet covered.
- **task-create-minimal-payload** — passed (87.7ms) — Checks that optional fields (description, milestone, assignee, etc.) are truly optional — validates schema defaults.
- **task-complete-marks-done** — passed (86.9ms) — State transition test — verifies task lifecycle works end-to-end, not just create/read.
- **task-archive-removes-from-active-list** — passed (88.2ms) — Verifies archival removes task from default task_list results — soft-delete semantics.
- **milestone-view-specific** — passed (86.3ms) — milestone_view not yet exercised — verifies individual milestone retrieval.
- **milestone-close-lifecycle** — passed (85.9ms) — Tests milestone state transition — milestone lifecycle is untested beyond create/list.
- **document-list-returns-created-doc** — passed (86.3ms) — document_list not yet called — verifies the document created in round 1 appears in listing.
- **document-update-body** — passed (89.2ms) — document_update is untested — verifies document content mutation persists correctly.
- **dist-build-freshness-check** — passed (10.5ms) — Previous dist-build-is-fresh FAIL was ambiguous — verify dist/index.js has real content (non-empty build artifact)
- **document-view-specific** — passed (135.8ms) — document_view was never tested — need to verify it works and what args it requires
- **document-search-by-keyword** — passed (91.5ms) — document_search tool not yet covered — verify keyword search works across documents
- **task-view-nonexistent-id** — passed (91.1ms) — Error handling for invalid task IDs — should return a clear error, not crash
- **task-search-no-results** — passed (89.9ms) — Verify search gracefully returns empty results rather than erroring on no matches
- **task-create-with-priority-and-tags** — passed (87.8ms) — task_create was only tested with basic payload and full payload — verify priority + tags fields are accepted
- **milestone-list-after-close-shows-closed** — passed (85.6ms) — milestone_close passed but milestone_list was only tested without filter — verify closed milestones appear when include_closed is true
- **project-info-invalid-project-id** — passed (86.8ms) — project_info passed with valid ID — verify it returns a clear error (not a crash) for an unknown GUID
- **task-view-archived-task-still-accessible** — passed (131.9ms) — Archived tasks should still be viewable by ID — archive means remove from active list, not delete
- **task-create-with-milestone-association** — passed (91.3ms) — Milestone association is a core workflow — tasks should be linkable to milestones at creation
- **milestone-create-with-description** — passed (89.4ms) — Verify optional description field is accepted and stored on milestone create
- **milestone-close-already-closed-idempotent** — passed (89.3ms) — Closing an already-closed milestone should either be idempotent or return a clear error — not crash
- **task-edit-status-to-in-progress** — passed (91.0ms) — Status transitions beyond complete/archive — in-progress is a common intermediate state
- **project-set-same-path-twice** — passed (91.4ms) — Re-registering the same path should be idempotent and return the same GUID, not create a duplicate
- **task-search-empty-string** — passed (90.1ms) — Empty string search — should return all tasks, a clear error, or gracefully handle rather than crash
- **document-update-nonexistent-id** — passed (92.9ms) — Error handling parity — task_view handles nonexistent IDs gracefully; document_update should too
- **task-create-special-chars-title** — passed (94.4ms) — Special characters in titles (HTML, quotes, em-dashes) must survive the round-trip without corruption
- **dist-build-is-fresh-recheck** — passed (6.9ms) — Previous round failed this check — re-verify whether source files are newer than the dist build, which would mean the build is stale
- **milestone-view-nonexistent-id** — passed (133.9ms) — milestone_view with bad ID should return a clear error, not a crash — symmetrical with task_view_nonexistent which already passed
- **task-list-filter-by-status** — passed (90.1ms) — task_list likely supports status filtering — untested; verify it returns only in-progress tasks and doesn't blow up on a valid filter param
- **task-create-invalid-priority** — passed (88.8ms) — invalid enum value for priority — should reject with validation error, not silently accept or crash
- **project-init-already-initialized** — passed (96.1ms) — calling project_init on an already-initialized project — should be idempotent (return same GUID) or give a clear 'already exists' error, not corrupt state
- **milestone-close-nonexistent** — passed (91.7ms) — milestone_close on a nonexistent milestone — should error cleanly, not silently succeed or crash
- **task-edit-no-fields** — passed (90.8ms) — task_edit with only required fields and no optional update fields — should either no-op gracefully or return a validation error, not crash
- **document-search-no-results** — passed (90.1ms) — document_search with zero results — verify it returns an empty list rather than an error, symmetric with task_search_no_results which passed
- **task-create-missing-title** — passed (89.7ms) — task_create without the required title field — should return a clear validation error, not a confusing crash or a task with an empty title

## What's broken
- **dist-build-is-fresh**
  - Output does not contain '1'
  - Why this matters: Checks that dist/ was compiled after the last source change. A stale build is a common source of 'tests pass locally but behavior is wrong' bugs.

## Probable root causes
- dist/index.js was not recompiled after recent source changes — 5 source files are newer than the build artifact
- The freshness check logic was inconsistent between rounds: first round checked for '1' newer file (ambiguous), second round checked for non-empty dist (always true), masking the real stale-build condition

## What to do about it
- Run `npm run build` (or equivalent TypeScript compile step) in /Users/dshanklinbv/repos-eidos-agi/ike.md to regenerate dist/index.js from current source
- Fix the dist-build-is-fresh test to check `find src -newer dist/index.js | wc -l` and assert output is '0', not '1' — the test passed a flaky recheck that used different criteria and masked the real staleness

## Watch out for
- 302 on authenticated endpoints is correct behavior, not a failure
- 405 means wrong HTTP method, not a broken endpoint
- 422 on POST without body means validation is working correctly

## When it's fixed
All 51 checks should pass. Specifically:
- dist-build-is-fresh should pass

## For the next robot

**Test suite:** `/Users/dshanklinbv/repos-eidos-agi/ike.md/.test-forge/suites/Users-dshanklinbv-repos-eidos-agi-ike.md.yaml` — run `test_this("/Users/dshanklinbv/repos-eidos-agi/ike.md")` to execute it.
The suite is the artifact. It persists. Add to it, don't start over.

**To retest:** `test_this("/Users/dshanklinbv/repos-eidos-agi/ike.md")` or `test_this("/Users/dshanklinbv/repos-eidos-agi/ike.md", playbook="security")`
