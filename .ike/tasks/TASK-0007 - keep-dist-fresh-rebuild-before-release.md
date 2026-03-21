---
id: TASK-0007
title: Keep dist/ fresh — rebuild before release
status: To Do
created: '2026-03-21'
priority: medium
milestone: MS-0002
tags:
  - evergreen
  - regression
  - ci
definition-of-done:
  - dist/ is never older than src/
  - 'Either: pre-push hook runs npm run build, or CI fails on stale dist'
---
test-forge caught that dist/ was stale (source newer than compiled output). npm run build must be run after any src/ change before pushing or publishing. Add a pre-push hook or CI step to enforce this.
