---
id: "GUARD-001"
type: "guardrail"
title: "ike.md must contain zero lines of backlog.md source code"
status: "active"
date: "2026-03-21"
---

## Rule
No code from the backlog.md repository may appear in ike.md. Inspiration is credited. Code is earned.

## Why
We chose a clean build specifically to avoid upstream architectural debt and license entanglement. The moment forked code appears, we inherit backlog.md's assumptions — CWD detection, single-project design, CLI-init — exactly what ike.md exists to replace.

## Violation Examples
- Copying any function, class, or utility from MrLesk/Backlog.md
- Adapting backlog.md code with variable renames
- Using backlog.md's markdown parser, ID generator, or filesystem walker verbatim
