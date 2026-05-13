# Migrating from `ike` to `docket`

`ike-md` was renamed to `docket-md` on 2026-05-13. The tool's behavior is unchanged; only the identifiers move. This guide walks you through migrating a project that was using `ike-md`.

## What changed

| Layer | Before | After |
|-------|--------|-------|
| PyPI package | `ike-md` | `docket-md` |
| CLI entries | `ike-md`, `ike-daemon` | `docket-md`, `docket-daemon` |
| Python module | `ike_md` | `docket_md` |
| MCP server name | `ike.md` | `docket.md` |
| MCP tool prefix | `mcp__ike__*` | `mcp__docket__*` |
| Project state dir | `.ike/` | `.docket/` |
| Project config file | `.ike/ike.json` | `.docket/docket.json` |
| Config field | `ike_path` | `docket_path` |
| User config root | `~/.config/ike/` | `~/.config/docket/` |
| launchd plist | `com.ike.daemon` | `com.docket.daemon` |

The old PyPI package `ike-md` will not be deleted. PyPI policy prohibits name reuse, so `ike-md` remains in its final state for historical access. New work installs `docket-md` instead.

The GitHub repo `eidos-agi/ike.md` was renamed to `eidos-agi/docket.md`. The old URL redirects for `git clone/fetch/push` and issue links, but **do not create a new repo named `ike.md`** under `eidos-agi` — that would permanently break the redirect.

## Recommended path: the migration script

The renamed package ships with a migration command. Install `docket-md`, then run it against any project that has a `.ike/` directory.

```bash
# 1. Install the renamed package
uv tool install docket-md
# or: pip install docket-md

# 2. Migrate a single project
cd /path/to/your-project
docket-migrate

# 2b. Or migrate many projects in one sweep
docket-migrate --root ~/repos-eidos-agi
```

The script is **idempotent** and **dry-run by default**. It prints what it would change. Pass `--apply` to actually rewrite. Each project gets:

1. `.ike/` → `.docket/` (directory rename, all task/milestone files preserved)
2. `.ike/ike.json` → `.docket/docket.json` (file rename, `ike_path` key renamed to `docket_path`, `project` field updated if it referenced the brand)
3. `.claude/settings.local.json`: all `mcp__ike__` entries become `mcp__docket__`
4. `.mcp.json`: any `"ike"` server name becomes `"docket"`; `command: "ike-md"` becomes `command: "docket-md"`

Files NOT touched:
- Markdown task content (preserved as-is)
- Anything outside the project root
- Any file containing the literal word `wrike` (different tool — Wrike SaaS integration)

## Manual path (if you don't want to use the script)

For a single project:

```bash
cd /path/to/your-project

# Rename the state directory
mv .ike .docket

# Rename the config file
mv .docket/ike.json .docket/docket.json

# Edit the config: rename the key and update the brand reference
python3 -c "
import json, pathlib
p = pathlib.Path('.docket/docket.json')
d = json.loads(p.read_text())
if 'ike_path' in d:
    d['docket_path'] = d.pop('ike_path').replace('.ike', '.docket')
if d.get('project') == 'ike.md':
    d['project'] = 'docket.md'
p.write_text(json.dumps(d, indent=2))
"

# Update Claude settings (replace mcp__ike__ with mcp__docket__)
if [ -f .claude/settings.local.json ]; then
    sed -i.bak 's/mcp__ike__/mcp__docket__/g' .claude/settings.local.json
    rm .claude/settings.local.json.bak
fi

# Update .mcp.json if present
if [ -f .mcp.json ]; then
    sed -i.bak \
        -e 's/"ike":/"docket":/g' \
        -e 's|"ike-md"|"docket-md"|g' \
        -e 's|"ike-daemon"|"docket-daemon"|g' \
        .mcp.json
    rm .mcp.json.bak
fi
```

## Verification

After migration:

```bash
# 1. State directory exists at new name, old one is gone
test -d .docket && test ! -d .ike && echo "OK: dir renamed"

# 2. Config file is at new name with correct field
test -f .docket/docket.json && \
    grep -q docket_path .docket/docket.json && \
    echo "OK: config migrated"

# 3. Claude can find the docket tools
grep -c mcp__docket__ .claude/settings.local.json 2>/dev/null
grep -c mcp__ike__ .claude/settings.local.json 2>/dev/null  # should be 0
```

If you've already started a Claude Code session, restart it so it picks up the renamed MCP server.

## User-level config

If you set anything in `~/.config/ike/settings.json` (org-level or repo-level overrides), copy that tree:

```bash
if [ -d ~/.config/ike ] && [ ! -d ~/.config/docket ]; then
    cp -r ~/.config/ike ~/.config/docket
fi
```

You can leave `~/.config/ike/` in place; nothing reads from it after migration. Or delete it once you've verified the new path works.

## If something breaks

The most common issue is a Claude session that started before the rename — it still has the old MCP tool names cached in its prompt context. Restart the session.

The second most common issue is a `.mcp.json` somewhere that references `ike-md` by path or pip install. The migration script catches `.mcp.json` files in the project root, but not in `~/.claude/` or elsewhere. Grep for stray references:

```bash
grep -rn "ike-md\|ike_md\|mcp__ike__\|\.ike/" ~/.claude/ 2>/dev/null
```

## Why this rename happened

See `decisions/[ADR-003]` in cockpit-eidos for the full reasoning. Short version: the Eidos trilogy was rebranded as `research / Governor / Docket` for clarity. The original plan was to keep `ike` as an internal codename (Twitter→X pattern) and only rebrand the user-facing surface. That plan was wrong for solo-scale infra where AI agents are the primary readers — every agent has to bridge "Docket says X, tool says ike" on every turn. The full rename fixes that.
