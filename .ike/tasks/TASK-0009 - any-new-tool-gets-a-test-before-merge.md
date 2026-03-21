---
id: TASK-0009
title: Any new tool gets a test before merge
status: To Do
created: '2026-03-21'
priority: high
milestone: MS-0002
tags:
  - evergreen
  - regression
  - process
definition-of-done:
  - >-
    Every tool has at least one test covering its filesystem side-effect or
    error path
  - 'Test count only goes up, never down'
---
Standing rule: adding a tool to server.ts requires at least one test covering the new behavior. No tool ships untested.
