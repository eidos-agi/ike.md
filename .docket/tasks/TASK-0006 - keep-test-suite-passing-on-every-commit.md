---
id: TASK-0006
title: Keep test suite passing on every commit
status: To Do
created: '2026-03-21'
priority: high
milestone: MS-0002
tags:
  - evergreen
  - regression
definition-of-done:
  - npm test passes 49/49 (or more) after every change
  - No skipped or commented-out tests
  - New behavior = new test before merging
---
npm test must pass before any push. If a test breaks, fix it before merging. This is a standing commitment — not a one-time task.
