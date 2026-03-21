# ike.md

> **The execution forge.** Tasks, milestones, documents, Definition of Done.

Named for Eisenhower — the man who planned D-Day and then ran the free world. Ike didn't just plan. He executed at scale, across many agents, under time pressure, with contracts that had to be honored.

---

## The Trilogy

ike.md is the third leg of a three-tool system for AI-driven work:

| Tool | Role | When to use |
|------|------|-------------|
| **research.md** | Decide with evidence | Before making architectural choices |
| **visionlog** | Record vision, goals, guardrails, ADRs | Contracts all execution must honor |
| **ike.md** | Execute within those contracts | Daily work: tasks, milestones, docs |

The trilogy is one loop with three stages:

```
research.md  →  visionlog  →  ike.md
  DECIDE        CONTRACT      EXECUTE
     ↑                           │
     └───────────────────────────┘
          execution reveals gaps
```

When ike.md reveals that a strategy is wrong — a task fails, a pattern repeats, a direction proves misguided — the feedback loop doesn't short-circuit back to visionlog directly. It goes all the way back to research.md:

1. **ike.md** — execution surfaces a gap or contradiction
2. **research.md** — earn the new answer with evidence before acting on it
3. **visionlog** — record the decision as an ADR
4. **ike.md** — execute the new direction

Skipping research.md means ADRs written under pressure, strategy updated on instinct, decisions that contradict each other three sessions later. The loop must complete fully to be trustworthy.

**Session protocol:** Read visionlog first (it tells you where the ladder points and what you must not cross). Then open ike.md and work. If execution reveals a gap in strategy, go back to research.md before updating visionlog.

---

## Install

```bash
# Clone
git clone git@github.com:eidos-agi/ike.md.git
cd ike.md
npm install
npm run build
```

Add to your `.mcp.json`:

```json
{
  "mcpServers": {
    "ike": {
      "type": "stdio",
      "command": "node",
      "args": ["/absolute/path/to/ike.md/dist/index.js"]
    }
  }
}
```

---

## GUID Workflow

ike.md uses a **stable GUID registry** — not fragile CWD scanning.

1. **New project:** `project_init` → writes `.ike/ike.json` with a stable GUID
2. **Existing project:** `project_set` → registers path→GUID in session memory
3. **Every other call:** pass `project_id` (the GUID)

If you forget the GUID, the error message tells you exactly what to call to recover.

---

## File Structure

```
your-project/
└── .ike/
    ├── ike.json          ← project config + stable GUID
    ├── tasks/            ← active tasks (TASK-0001 - slug.md)
    ├── completed/        ← Done tasks
    ├── archive/          ← Cancelled / superseded tasks
    ├── milestones/       ← MS-0001 - slug.md
    └── documents/        ← DOC-0001 - slug.md
```

All files are plain markdown with YAML frontmatter — readable without ike.md.

---

## Tool Reference

### Project
| Tool | What |
|------|------|
| `project_init` | Initialize new project, get GUID |
| `project_set` | Register existing project for session |
| `project_list` | List registered projects |
| `project_info` | Stats: task counts, milestones, docs |

### Tasks
| Tool | What |
|------|------|
| `task_create` | Create task with optional priority, milestone, DoD |
| `task_list` | List with status/milestone/assignee/tag filters |
| `task_view` | Full detail for one task |
| `task_edit` | Update any field; append notes |
| `task_complete` | Mark Done, move to completed/ |
| `task_archive` | Cancel/supersede, move to archive/ |
| `task_search` | Keyword search across title + notes |

### Milestones
| Tool | What |
|------|------|
| `milestone_create` | New milestone with optional due date |
| `milestone_list` | All milestones (open + closed) |
| `milestone_view` | Full detail |
| `milestone_close` | Mark complete |

### Documents
| Tool | What |
|------|------|
| `document_create` | New doc with content + tags |
| `document_list` | All documents |
| `document_view` | View by DOC-XXXX |
| `document_update` | Replace or append content |

---

## Task Frontmatter

```yaml
---
id: TASK-0001
title: Build the thing
status: To Do         # To Do | In Progress | Done | Draft
priority: high        # high | medium | low
milestone: MS-0001
assignees: [daniel]
tags: [infra, core]
dependencies: [TASK-0000]
acceptance-criteria:
  - Users can log in
definition-of-done:
  - Tests passing
  - Deployed to staging
created: 2026-03-20
updated: 2026-03-20
---

Notes go here as markdown body.
```

---

## Philosophy

Tasks without contracts drift. Contracts without tasks are wishes.

ike.md is where the two meet. Before you create a task, the visionlog guardrail has already told you what you cannot do. The Definition of Done field is the contract written before the work begins — machine-checkable, not vibes.

19 tools across project, task, milestone, and document management. Inspired by [backlog.md](https://github.com/MrLesk/Backlog.md). Zero forked code. Full credit for the concept.

---

MIT License © 2025 Daniel Shanklin
