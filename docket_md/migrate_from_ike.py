"""docket-migrate — rename `ike-md` state to `docket-md` in any project.

Run inside a project directory (looks for `.ike/`) or pass `--root` to sweep
a tree of repos. Dry-run by default; pass `--apply` to actually rewrite.

Renames performed per project:
    .ike/                       -> .docket/
    .ike/ike.json               -> .docket/docket.json
        key `ike_path`          -> `docket_path` (value also updated)
        field `project: ike.md` -> `project: docket.md`
    .claude/settings.local.json: mcp__ike__ -> mcp__docket__
    .mcp.json:                   ike-md / ike_md / ike-daemon refs,
                                 server-name `"ike"` -> `"docket"`

Files NEVER touched:
    - Anything containing 'wrike' (Wrike SaaS integration, different tool)
    - Markdown task content (only filenames are preserved via dir rename)
    - Files outside the project root
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Plan:
    project_root: Path
    actions: list[tuple[str, str]]  # (description, detail)

    def add(self, description: str, detail: str = "") -> None:
        self.actions.append((description, detail))

    def is_empty(self) -> bool:
        return not self.actions


def _safe_sub(content: str, pattern: str, replacement: str) -> tuple[str, int]:
    """Substitute, returning the new content and number of changes."""
    new_content, n = re.subn(pattern, replacement, content)
    return new_content, n


def plan_for_project(project_root: Path) -> Plan:
    plan = Plan(project_root, [])
    ike_dir = project_root / ".ike"
    docket_dir = project_root / ".docket"

    if ike_dir.is_dir() and not docket_dir.exists():
        plan.add(f"rename {ike_dir.name}/ -> {docket_dir.name}/")

    # Config JSON
    ike_json = ike_dir / "ike.json" if ike_dir.is_dir() else None
    if ike_json and ike_json.is_file():
        plan.add(f"rename {ike_dir.name}/ike.json -> {docket_dir.name}/docket.json")
        try:
            data = json.loads(ike_json.read_text())
        except Exception as e:
            plan.add(f"  WARN: could not parse JSON ({e}); will copy raw")
            data = None
        if isinstance(data, dict):
            if "ike_path" in data:
                plan.add(
                    f"  set docket_path={data['ike_path'].replace('.ike', '.docket')!r} (was ike_path)"
                )
            if data.get("project") == "ike.md":
                plan.add("  set project='docket.md' (was 'ike.md')")

    # Claude settings allowlist
    settings = project_root / ".claude" / "settings.local.json"
    if settings.is_file():
        content = settings.read_text()
        _, n = _safe_sub(content, r"mcp__ike__", "mcp__docket__")
        if n:
            plan.add(
                f"edit .claude/settings.local.json: {n} mcp__ike__ -> mcp__docket__"
            )

    # .mcp.json server name + commands
    mcp_json = project_root / ".mcp.json"
    if mcp_json.is_file():
        content = mcp_json.read_text()
        change_count = 0
        _, n = _safe_sub(content, r'"ike"\s*:', '"docket":')
        change_count += n
        _, n = _safe_sub(content, r'"ike-md"', '"docket-md"')
        change_count += n
        _, n = _safe_sub(content, r'"ike-daemon"', '"docket-daemon"')
        change_count += n
        _, n = _safe_sub(content, r"ike_md\.", "docket_md.")
        change_count += n
        if change_count:
            plan.add(f"edit .mcp.json: {change_count} ike-* identifiers -> docket-*")

    return plan


def apply_plan(plan: Plan) -> None:
    project_root = plan.project_root
    ike_dir = project_root / ".ike"
    docket_dir = project_root / ".docket"

    # 1. Rename .ike/ -> .docket/
    if ike_dir.is_dir() and not docket_dir.exists():
        ike_dir.rename(docket_dir)

    # 2. Rename ike.json -> docket.json + edit fields
    ike_json = docket_dir / "ike.json"  # now in renamed dir
    docket_json = docket_dir / "docket.json"
    if ike_json.is_file():
        try:
            data = json.loads(ike_json.read_text())
        except Exception:
            data = None
        if isinstance(data, dict):
            if "ike_path" in data:
                data["docket_path"] = data.pop("ike_path").replace(".ike", ".docket")
            if data.get("project") == "ike.md":
                data["project"] = "docket.md"
            docket_json.write_text(json.dumps(data, indent=2))
            ike_json.unlink()
        else:
            # Couldn't parse — preserve content by raw move
            shutil.move(str(ike_json), str(docket_json))

    # 3. Claude settings allowlist
    settings = project_root / ".claude" / "settings.local.json"
    if settings.is_file():
        content = settings.read_text()
        new, _ = _safe_sub(content, r"mcp__ike__", "mcp__docket__")
        if new != content:
            settings.write_text(new)

    # 4. .mcp.json
    mcp_json = project_root / ".mcp.json"
    if mcp_json.is_file():
        content = mcp_json.read_text()
        new = content
        new, _ = _safe_sub(new, r'"ike"\s*:', '"docket":')
        new, _ = _safe_sub(new, r'"ike-md"', '"docket-md"')
        new, _ = _safe_sub(new, r'"ike-daemon"', '"docket-daemon"')
        new, _ = _safe_sub(new, r"ike_md\.", "docket_md.")
        if new != content:
            mcp_json.write_text(new)


def find_projects(root: Path) -> list[Path]:
    """Find directories containing .ike/ under root (depth-limited)."""
    found = []
    for path in root.rglob(".ike"):
        if path.is_dir():
            parent = path.parent
            # Skip if .docket/ also exists — likely already migrated mirror
            if (parent / ".docket").exists():
                continue
            found.append(parent)
    return sorted(found)


def main() -> int:
    p = argparse.ArgumentParser(
        prog="docket-migrate",
        description="Migrate a project from ike-md state to docket-md state.",
    )
    p.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Sweep all projects under this root. Default: just the current directory.",
    )
    p.add_argument(
        "--apply",
        action="store_true",
        help="Actually rewrite. Without this, runs as a dry-run.",
    )
    args = p.parse_args()

    if args.root:
        if not args.root.is_dir():
            print(f"--root {args.root} is not a directory", file=sys.stderr)
            return 2
        projects = find_projects(args.root)
        if not projects:
            print(f"No .ike/ directories under {args.root}.")
            return 0
        print(f"Found {len(projects)} project(s) with .ike/ under {args.root}.\n")
    else:
        cwd = Path.cwd()
        if not (cwd / ".ike").is_dir():
            print(f"No .ike/ in {cwd}. Nothing to migrate.")
            print("Use --root to sweep a directory tree.")
            return 0
        projects = [cwd]

    plans = [plan_for_project(p) for p in projects]
    nonempty = [pl for pl in plans if not pl.is_empty()]

    if not nonempty:
        print("Nothing to migrate.")
        return 0

    for plan in nonempty:
        print(f"\n=== {plan.project_root} ===")
        for desc, _ in plan.actions:
            print(f"  • {desc}")

    if not args.apply:
        print(f"\n(dry-run; pass --apply to rewrite {len(nonempty)} project(s))")
        return 0

    for plan in nonempty:
        apply_plan(plan)
        print(f"migrated: {plan.project_root}")

    print(f"\nDone. Migrated {len(nonempty)} project(s).")
    print(
        "Restart any active Claude Code sessions so they pick up the renamed MCP server."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
