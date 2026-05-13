# RFC-001: Session-Aware docket-daemon

## Core Primitives

Two lists. Everything else is derived.

### 1. The Hot List (sessions)

Every JSONL file started or modified in the last 7 days. This is the daemon's watch list. Populated by the `SessionStart` hook, which fires on every Claude Code session and writes `{session_id, jsonl_path, cwd}` to a queue file. The daemon reads the queue and adds entries to the hot list.

Activity resets the TTL. A 30-day-old session that gets resumed and has new bytes → back on the hot list. A session with no activity for 7 days → pruned.

The hot list is: **what to watch.**

### 2. The Link List (session × project)

Every confirmed association between a session_id and a project_id. Built by detecting `project_set` and `project_init` tool calls in the JSONL streams. Many-to-many: one session can link to multiple projects, one project can be linked from multiple sessions.

The link list is: **where to route.**

## The Flush Problem

Claude Code buffers JSONL writes. When `project_set` runs in the MCP server, the tool call entry is in memory, not on disk. The daemon can't find what hasn't been flushed.

This is why both sides use queues with exponential backoff.

### MCP server side

When `project_set` or `project_init` is called, it appends to `~/.config/docket/daemon-queue.jsonl`:

```json
{"type": "link_project", "project_id": "25eb3f59-...", "project_path": "/repos/cockpit-eidos", "queued_at": "2026-03-26T00:01:00Z"}
```

Both `project_set` (register existing) and `project_init` (create new) establish a session × project link. Both write the same queue entry. The daemon treats them identically.

This is the signal: "I just ran. The evidence is somewhere in a JSONL on the hot list. Go find it."

### Daemon side

The daemon picks up the `link_project` job and starts searching the hot list for a JSONL that contains a `project_set` or `project_init` call with that `project_id`.

First try — not there yet (buffered). Retry with exponential backoff:
- 5s → 10s → 20s → 40s → 60s (cap)
- Max 10 retries (~5 minutes of patience)

When found: the JSONL that contains the `project_set`/`project_init` call is the session. Extract `session_id` from the filename. Add to the link list: `{session_id, project_id, project_path, linked_at}`.

If never found after max retries: log a warning, drop the job. The JSONL was either never flushed or the session died.

## The Hook

Installed by `docket-daemon install` into `~/.claude/settings.json`:

```json
{
  "SessionStart": [{
    "matcher": "",
    "hooks": [{
      "type": "command",
      "command": "jq -c '{type:\"watch_session\",session_id:.session_id,jsonl:.transcript_path,cwd:.cwd}' >> ~/.config/docket/daemon-queue.jsonl",
      "timeout": 5
    }]
  }]
}
```

Fires on every session start. Writes to the same queue the MCP server uses. Three producers, one consumer.

## Data Flow

```
SESSION START
│
├─ Hook fires → queue: {type: "watch_session", session_id, jsonl_path}
│
├─ Daemon reads queue → adds to HOT LIST
│   (session_id → jsonl_path, ttl: 7 days from last activity)
│
│  ... session runs, agent works ...
│
├─ Agent calls docket.project_set(path) or docket.project_init(path)
│   ├─ MCP server registers/creates project (normal behavior)
│   └─ MCP server → queue: {type: "link_project", project_id, project_path}
│
├─ Daemon reads queue → starts searching HOT LIST
│   ├─ For each JSONL on hot list, grep tail for project_set + project_id
│   ├─ Not found? → exponential backoff, retry
│   ├─ Found? → extract session_id from filename
│   └─ Add to LINK LIST: session_id × project_id
│
│  ... agent continues working ...
│
├─ Agent approves a plan
│   ├─ "User has approved your plan" written to JSONL
│   ├─ Daemon reads new bytes (already watching this JSONL via hot list)
│   ├─ Detects plan approval event
│   ├─ Looks up session_id in LINK LIST → finds project_id(s)
│   └─ Routes plan to each linked project's .docket/plans/
│
└─ SESSION ENDS
    └─ JSONL stops growing → TTL clock starts
       └─ After 7 days of inactivity → pruned from hot list
```

## Many-to-Many

A session can call `project_set` multiple times for different projects. Each one produces a `link_project` queue entry. The daemon links the session to each project independently. The link list grows:

```
session_id: 02561bc3
  → cockpit-eidos (linked at 18:00)
  → eidos-mail (linked at 19:30)
  → eidos-capital (linked at 20:00)
```

When an event is detected in that session's JSONL:
- Check link list for this session_id
- Route to ALL linked projects? Or match based on event content?
- For plan approvals: the plan content may reference a specific project. Use the most recently linked project as default, with content-based override if possible.
- For `task_complete` calls: the project_id is in the tool arguments. Route directly.

## .docket/sessions.json (per project)

Each project gets a view of the sessions that touched it:

```json
{
  "sessions": [
    {
      "id": "02561bc3-...",
      "first_seen": "2026-03-25T18:00:00Z",
      "last_activity": "2026-03-26T00:15:00Z",
      "status": "active",
      "jsonl": "/path/to/session.jsonl",
      "events": [
        {"type": "plan_approved", "plan_id": "PLAN-0001", "at": "..."},
        {"type": "plan_approved", "plan_id": "PLAN-0002", "at": "..."}
      ]
    }
  ]
}
```

The same session_id can appear in multiple projects' `sessions.json`. Each project only sees the events relevant to it.

## Daemon State

```json
{
  "hot_list": {
    "02561bc3-...": {
      "jsonl": "/path/to/session.jsonl",
      "offset": 9435803,
      "last_activity": "2026-03-26T00:15:00Z"
    }
  },
  "link_list": [
    {"session_id": "02561bc3-...", "project_id": "25eb3f59-...", "project_path": "/repos/cockpit-eidos", "linked_at": "..."}
  ],
  "pending_links": [
    {"project_id": "a1b2c3-...", "project_path": "/repos/eidos-mail", "queued_at": "...", "retries": 3, "next_retry": "..."}
  ],
  "ingested": ["session:title"]
}
```

Three sections:
- `hot_list`: what to watch (session_id → JSONL path + offset)
- `link_list`: confirmed links (session × project)
- `pending_links`: link_project jobs still searching (exponential backoff)

## CLI

```
docket-daemon install     Add SessionStart hook to ~/.claude/settings.json
docket-daemon start       Start the polling loop
docket-daemon status      Show hot list, link list, pending links
docket-daemon stop        Stop the daemon
```

## Queue File

`~/.config/docket/daemon-queue.jsonl` — append-only, three producers (hook, project_set, project_init):

```jsonl
{"type":"watch_session","session_id":"02561bc3-...","jsonl":"/path/to/session.jsonl","cwd":"/Users/..."}
{"type":"link_project","project_id":"25eb3f59-...","project_path":"/repos/cockpit-eidos","queued_at":"2026-03-26T00:01:00Z"}
```

Daemon reads all lines, processes them, truncates. `watch_session` → hot list. `link_project` → pending_links (starts backoff search).

## Event Detection & Routing

The daemon reads new bytes from each hot list JSONL on every poll cycle (30s). For each new line:

1. **Is it a `project_set` or `project_init` call?** → Extract project_id from tool arguments. Check if this session already has this link. If not, add to link list. (This is the fast path — daemon sees it directly in the stream, no backoff needed. The queue+backoff is the fallback for when the JSONL hasn't flushed yet.)

2. **Is it a plan approval?** → Look up this session's links. Route to the linked project(s). Create PLAN-XXXX in `.docket/plans/`, add event to `.docket/sessions.json`.

3. **Is it a `task_complete` call?** → Extract project_id from tool arguments. Route directly. Add event to `.docket/sessions.json`.

4. **Is it any other docket tool call?** → Can be used to update `last_activity` on the session entry.

Detection happens in the stream. Routing uses the link list. Both are in the same read loop.

## What Changes from Current Implementation

| Current (v1) | This RFC (v2) |
|---|---|
| Scans all recent JONLs globally | Hot list: only watches sessions registered by hook |
| Links session to project by cwd at registration | Link list: session × project via project_set detection |
| One-to-one: session belongs to one project | Many-to-many: session can link to multiple projects |
| No retry on flush delay | Exponential backoff for pending links |
| Queue has one producer (hook) | Queue has three producers (hook + project_set + project_init) |
| State: offsets only | State: hot list + link list + pending links |

## Implementation Order

1. Update `project_set` AND `project_init` in server.py to append `link_project` to queue (~5 lines each)
2. Rewrite daemon state to use hot_list / link_list / pending_links
3. Add pending link processing with exponential backoff
4. Add `project_set` detection in the stream reader (fast path)
5. Route plan approvals through link list instead of cwd
6. Update sessions.json to support many-to-many
7. Tests
8. Manual end-to-end test

## Open Questions

1. **Plan routing ambiguity:** If a session is linked to 3 projects and a plan is approved, which project gets the plan? Options: (a) most recently linked project, (b) all linked projects, (c) match based on plan content/cwd on the approval entry. Recommend (a) with (c) as override.

2. **Retroactive routing:** If a plan is approved BEFORE `project_set` is called (orphaned event), should the daemon retroactively route it when the link is established? Recommend yes — replay unrouted events when a new link is confirmed.

3. **Hot list initial population:** On first daemon start, should it scan for recently modified JONLs to seed the hot list? Or only watch sessions registered by the hook going forward? Recommend: seed from recently modified files (last 1 hour only) to catch sessions started just before the daemon.
