---
title: "ike.md — The Execution Forge"
type: "vision"
date: "2026-03-21"
---

`ike.md` is a modern AI-native execution forge — the third member of the Eidos trilogy alongside `research.md` (decide) and `visionlog` (contract).

Named for Eisenhower — the man who planned D-Day and then ran the free world. Ike didn't just plan. He executed at scale, across many agents, under time pressure, with contracts that had to be honored.

## The trilogy

```
research.md  →  visionlog  →  ike.md
  DECIDE        CONTRACT      EXECUTE
```

## ike.md is the Execution Forge

A forge is the loop (PERCEIVE → DECOMPOSE → SPECIALIZE → ACT → COMPRESS → VERIFY → LEARN → RETRY) instantiated at domain scale. ike.md is the **Execution Forge** — its domain is task execution, and its primary loop is:

```
ACT (run the task) → VERIFY (check the contract)
```

Its artifact is a completed task. The Definition of Done is the contract for VERIFY — machine-checkable, written before execution begins, evaluated independently of the executor.

**What ike.md is:** the ACT and VERIFY stages of the forge, applied to tasks. Phase gates enforce lifecycle transitions. DoD items are the finish line, not the executor's self-assessment.

**What ike.md is not yet:** the full forge. PERCEIVE, DECOMPOSE, SPECIALIZE, COMPRESS, LEARN, and RETRY happen elsewhere — in the agent, in the orchestrator, in the human.

## The Contract Is the Missing Step

VERIFY is broken in most AI workflows because the executor self-assesses. "It works" means "I checked and it passes my own test." That is not verification — it is rationalization.

The contract (Definition of Done) must be:
- Written before execution begins
- Machine-checkable where possible
- Evaluated independently of the executor

ike.md enforces this: DoD items gate task completion. A task is not done because the agent says it is done. It is done when the DoD is satisfied.

## North Star

An agent (or human) can pick up any task in any project and know exactly:
1. What "done" looks like (DoD)
2. What constraints apply (visionlog guardrails)
3. What decisions were made and why (visionlog ADRs)
4. What the current execution state is (ike task board)

No context required beyond what ike.md and visionlog provide.

