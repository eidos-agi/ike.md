"""Config inspection: get, set, tree, where."""

from __future__ import annotations

import json

from ..config import list_registered, load_config, resolve_project
from ..hier_config import (
    deep_merge,
    find_setting_origin,
    get_config_tree,
    resolve_config_chain,
    set_value as _hc_set_value,
)


def config_get(project_id: str | None = None, path: str | None = None) -> str:
    """Show resolved settings for a project path, with inheritance visible."""
    if project_id:
        path = resolve_project(project_id)
    if not path:
        registered = list_registered()
        if registered:
            path = registered[0]["path"]
        else:
            return "No project registered and no path provided."

    chain = resolve_config_chain(path)
    merged: dict = {}
    lines = ["## Config Resolution\n"]
    for level_name, settings_path, settings in chain:
        lines.append(f"**{level_name}** `{settings_path}`")
        if settings:
            lines.append(f"```json\n{json.dumps(settings, indent=2)}\n```")
        else:
            lines.append("_(empty)_")
        merged = deep_merge(merged, settings)

    lines.append("\n**Resolved (merged):**")
    lines.append(f"```json\n{json.dumps(merged, indent=2)}\n```")
    return "\n".join(lines)


def config_set(
    key: str,
    value: str,
    level: str = "project",
    project_id: str | None = None,
    path: str | None = None,
) -> str:
    """Set a config value at a specific level."""
    if project_id:
        path = resolve_project(project_id)
    if not path:
        registered = list_registered()
        if registered:
            path = registered[0]["path"]
        else:
            return "No project registered and no path provided."

    try:
        parsed = json.loads(value)
    except (json.JSONDecodeError, TypeError):
        parsed = value

    pid = None
    if project_id:
        pid = project_id
    else:
        cfg = load_config(path)
        if cfg:
            pid = cfg.id

    sp = _hc_set_value(path, key, parsed, level=level, project_id=pid)
    return f"Set `{key}` = `{parsed}` at **{level}** level\nFile: `{sp}`"


def config_tree() -> str:
    """Show the entire ~/.config/docket/ settings tree."""
    tree = get_config_tree()
    if not tree:
        return "No config tree found at ~/.config/docket/"
    return f"## Config Tree\n\n```json\n{json.dumps(tree, indent=2)}\n```"


def config_where(
    key: str, project_id: str | None = None, path: str | None = None
) -> str:
    """Show which level set a specific config key."""
    if project_id:
        path = resolve_project(project_id)
    if not path:
        registered = list_registered()
        if registered:
            path = registered[0]["path"]
        else:
            return "No project registered and no path provided."

    pid = None
    if project_id:
        pid = project_id
    else:
        cfg = load_config(path)
        if cfg:
            pid = cfg.id

    result = find_setting_origin(key, path, project_id=pid)
    if result:
        level_name, val = result
        return f"`{key}` = `{val}` — set at **{level_name}** level"
    return f"`{key}` is not set at any level."
