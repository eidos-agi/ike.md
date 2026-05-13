# Trilogy Conventions

> Shared standards for **docket.md**, **visionlog.md**, and **research.md**.
>
> docket.md is the reference implementation. The other two implement against this document.

---

## Directory Convention

Each tool stores its state in a dot-prefixed directory at the project root:

| Tool | Directory | Config file |
|------|-----------|-------------|
| docket.md | `.docket/` | `.docket/docket.json` |
| visionlog.md | `.visionlog/` | `.visionlog/config.yaml` |
| research.md | `.research/` | `.research/research.json` |

**Dot-prefix** signals "tool metadata, not primary source code." It keeps the directory out of the way in file explorers and IDEs without hiding intent from collaborators.

**These directories are committed to git by default.** That is the point — tasks, decisions, and research findings persist across sessions, machines, and contributors via git history. Gitignoring them defeats their purpose.

The only reason to gitignore a trilogy directory is a deliberate local-only workflow (single-user, no collaboration, no history). That is the opt-in exception, not the default.

---

## Monorepo Support

In a monorepo, each sub-package that needs its own trilogy state initializes independently. There is no shared root — each sub-package's trilogy tool is initialized at its own directory:

```
my-monorepo/
├── packages/
│   ├── api/
│   │   ├── .docket/          ← api's tasks
│   │   └── .visionlog/    ← api's decisions
│   └── web/
│       ├── .docket/          ← web's tasks
│       └── .visionlog/    ← web's decisions
```

Each produces its own GUID. Cross-package dependencies are expressed via task `dependencies` fields referencing the other package's task IDs.

---

## GUID Routing

Every trilogy tool uses stable GUID routing. This prevents fragile CWD-scanning and allows multiple projects to be registered in a single session.

**Standard tool names:**

| Operation | Tool name |
|-----------|-----------|
| Initialize new project | `project_init` |
| Register existing project for session | `project_set` |
| List registered projects | `project_list` |
| Project stats | `project_info` |

**Standard parameter name:** `project_id` — the GUID returned by `project_init` or `project_set`, passed to every subsequent tool call.

**Session protocol:**
1. Call `project_set` with the project path → get `project_id`
2. Pass `project_id` to every subsequent call
3. If the GUID is lost, call `project_set` again — it reads the GUID from the dot-dir config

**Error message standard:** If `project_id` is unknown or absent, the error must tell the caller exactly which tool to call to recover. No silent failures, no vague "project not found."

```
Unknown project_id 'abc-123'. Call project_set with the project path to register it.
```

---

## Config File Format

Each tool's config file contains at minimum:

```json
{
  "id": "<uuid-v4>",
  "project": "<human-readable name>",
  "created": "<ISO 8601 date>"
}
```

The `id` field is written once at `project_init` and never overwritten. It is the stable GUID that survives renames, moves, and re-inits.

---

## What This Is Not

- **Not a gitignore convention.** Dot-dir ≠ ignored. Commit these.
- **Not a lock file.** These directories are human-readable markdown and JSON/YAML. Read them directly if the MCP server is unavailable.
- **Not tool-specific configuration.** Each tool's dot-dir contains only that tool's state. No cross-tool coupling at the filesystem level.
