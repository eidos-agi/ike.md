---
id: TASK-0013
title: Package and publish ike.md for global distribution
status: To Do
created: '2026-03-21'
priority: medium
tags:
  - trilogy
  - distribution
  - ike
dependencies:
  - TASK-0011
definition-of-done:
  - Installable with one command on any machine
  - Listed in npm or PyPI
  - README install section updated
  - Wired into global MCP config via npx/uvx
---
Once distribution format is decided (TASK-0011), package ike.md for global install. If npm: publish @eidos-agi/ike-md, update install docs to use npx. If Python rewrite: port to FastMCP, publish to PyPI.
