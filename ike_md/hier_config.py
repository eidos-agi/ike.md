"""Hierarchical config resolution for ike.md.

Settings live in ~/.config/ike/ as a folder tree that mirrors the project
hierarchy: global → org → repo → project. Each level has an optional
settings.json. Resolution merges top-down; child overrides parent.

    ~/.config/ike/
      settings.json                          # global defaults
      orgs/
        aic-holdings/
          settings.json                      # org-level
          repos/
            ciso/
              settings.json                  # repo-level
              projects/
                <project-uuid>/
                  settings.json              # project-level
"""

import json
import os
import re
import subprocess
from typing import Any


IKE_CONFIG_ROOT = os.path.expanduser("~/.config/ike")


# ---------------------------------------------------------------------------
# Deep merge
# ---------------------------------------------------------------------------

def deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge *override* into *base*. Child wins on conflicts."""
    result = dict(base)
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = deep_merge(result[k], v)
        else:
            result[k] = v
    return result


# ---------------------------------------------------------------------------
# Git remote helpers
# ---------------------------------------------------------------------------

def _git_root(path: str) -> str | None:
    """Walk up from *path* looking for a .git/ directory."""
    current = os.path.abspath(path)
    while True:
        if os.path.isdir(os.path.join(current, ".git")):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            return None
        current = parent


def _git_remote_url(git_root: str) -> str | None:
    """Get the origin remote URL, or None."""
    try:
        result = subprocess.run(
            ["git", "-C", git_root, "remote", "get-url", "origin"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def parse_git_remote(url: str) -> tuple[str, str] | None:
    """Extract (org, repo) from a git remote URL.

    Handles:
        git@github.com:aic-holdings/ciso.git
        https://github.com/aic-holdings/ciso.git
        https://github.com/aic-holdings/ciso
    """
    # SSH: git@github.com:org/repo.git
    m = re.match(r"git@[^:]+:([^/]+)/([^/]+?)(?:\.git)?$", url)
    if m:
        return m.group(1), m.group(2)
    # HTTPS: https://github.com/org/repo.git
    m = re.match(r"https?://[^/]+/([^/]+)/([^/]+?)(?:\.git)?$", url)
    if m:
        return m.group(1), m.group(2)
    return None


def detect_org_repo(project_path: str) -> tuple[str | None, str | None]:
    """Detect org and repo from the git remote of the nearest .git/ ancestor."""
    git_root = _git_root(project_path)
    if not git_root:
        return None, None
    url = _git_remote_url(git_root)
    if not url:
        return None, None
    result = parse_git_remote(url)
    if not result:
        return None, None
    return result


# ---------------------------------------------------------------------------
# Settings I/O
# ---------------------------------------------------------------------------

def _ensure_dir(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)


def read_settings(settings_path: str) -> dict:
    """Read a settings.json. Returns {} if missing or malformed."""
    if not os.path.isfile(settings_path):
        return {}
    try:
        with open(settings_path) as f:
            return json.load(f)
    except Exception:
        return {}


def write_settings(settings_path: str, data: dict) -> None:
    """Write settings.json, creating parent dirs as needed."""
    _ensure_dir(settings_path)
    with open(settings_path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


# ---------------------------------------------------------------------------
# Config chain resolution
# ---------------------------------------------------------------------------

def _settings_path(*parts: str) -> str:
    return os.path.join(IKE_CONFIG_ROOT, *parts, "settings.json")


def resolve_config_chain(
    project_path: str,
    project_id: str | None = None,
) -> list[tuple[str, str, dict]]:
    """Return the ordered list of (level_name, settings_path, settings_dict)
    from global down to project level.

    *project_id* is the UUID from .ike/ike.json; pass it if already known.
    """
    chain: list[tuple[str, str, dict]] = []

    # 1. Global
    gp = _settings_path()
    chain.append(("global", gp, read_settings(gp)))

    # 2. Org + Repo (from git remote)
    org, repo = detect_org_repo(project_path)
    if org:
        op = _settings_path("orgs", org)
        chain.append(("org", op, read_settings(op)))
        if repo:
            rp = _settings_path("orgs", org, "repos", repo)
            chain.append(("repo", rp, read_settings(rp)))

    # 3. Project (by UUID)
    if not project_id:
        from .config import load_config
        cfg = load_config(project_path)
        if cfg:
            project_id = cfg.id

    if project_id and org and repo:
        pp = _settings_path("orgs", org, "repos", repo, "projects", project_id)
        chain.append(("project", pp, read_settings(pp)))

    return chain


def resolved_settings(
    project_path: str,
    project_id: str | None = None,
) -> dict:
    """Return the fully-merged settings for a project path."""
    chain = resolve_config_chain(project_path, project_id)
    result: dict = {}
    for _level, _path, settings in chain:
        result = deep_merge(result, settings)
    return result


# ---------------------------------------------------------------------------
# Set / get helpers
# ---------------------------------------------------------------------------

def _parse_dotted_key(key: str) -> list[str]:
    """Split 'wrike.enabled' into ['wrike', 'enabled']."""
    return key.split(".")


def _set_nested(d: dict, keys: list[str], value: Any) -> None:
    """Set a value in a nested dict using a list of keys."""
    for k in keys[:-1]:
        d = d.setdefault(k, {})
    d[keys[-1]] = value


def _get_nested(d: dict, keys: list[str]) -> Any:
    """Get a value from a nested dict. Returns None if path doesn't exist."""
    for k in keys:
        if not isinstance(d, dict) or k not in d:
            return None
        d = d[k]
    return d


def set_value(
    project_path: str,
    key: str,
    value: Any,
    level: str = "project",
    project_id: str | None = None,
) -> str:
    """Set a dotted key at a specific level. Returns the path written to."""
    org, repo = detect_org_repo(project_path)

    if level == "global":
        sp = _settings_path()
    elif level == "org":
        if not org:
            raise ValueError("Cannot determine org from git remote. Set it manually or add a git remote.")
        sp = _settings_path("orgs", org)
    elif level == "repo":
        if not org or not repo:
            raise ValueError("Cannot determine org/repo from git remote.")
        sp = _settings_path("orgs", org, "repos", repo)
    elif level == "project":
        if not project_id:
            from .config import load_config
            cfg = load_config(project_path)
            if cfg:
                project_id = cfg.id
        if not project_id or not org or not repo:
            raise ValueError("Cannot determine project-level config path. Ensure git remote and .ike/ike.json exist.")
        sp = _settings_path("orgs", org, "repos", repo, "projects", project_id)
    else:
        raise ValueError(f"Unknown level: {level}. Use global, org, repo, or project.")

    data = read_settings(sp)
    keys = _parse_dotted_key(key)
    _set_nested(data, keys, value)
    write_settings(sp, data)
    return sp


def find_setting_origin(
    key: str,
    project_path: str,
    project_id: str | None = None,
) -> tuple[str, Any] | None:
    """Find which level set a key. Returns (level_name, value) or None."""
    chain = resolve_config_chain(project_path, project_id)
    keys = _parse_dotted_key(key)
    origin = None
    for level_name, _path, settings in chain:
        val = _get_nested(settings, keys)
        if val is not None:
            origin = (level_name, val)
    return origin


# ---------------------------------------------------------------------------
# Tree inspection
# ---------------------------------------------------------------------------

def get_config_tree() -> dict:
    """Walk ~/.config/ike/ and return a nested representation of all settings."""
    tree: dict = {}
    root = IKE_CONFIG_ROOT
    if not os.path.isdir(root):
        return tree

    # Global
    gs = read_settings(os.path.join(root, "settings.json"))
    if gs:
        tree["global"] = gs

    orgs_dir = os.path.join(root, "orgs")
    if not os.path.isdir(orgs_dir):
        return tree

    for org_name in sorted(os.listdir(orgs_dir)):
        org_path = os.path.join(orgs_dir, org_name)
        if not os.path.isdir(org_path):
            continue
        org_entry: dict = {}
        org_settings = read_settings(os.path.join(org_path, "settings.json"))
        if org_settings:
            org_entry["_settings"] = org_settings

        repos_dir = os.path.join(org_path, "repos")
        if os.path.isdir(repos_dir):
            for repo_name in sorted(os.listdir(repos_dir)):
                repo_path = os.path.join(repos_dir, repo_name)
                if not os.path.isdir(repo_path):
                    continue
                repo_entry: dict = {}
                repo_settings = read_settings(os.path.join(repo_path, "settings.json"))
                if repo_settings:
                    repo_entry["_settings"] = repo_settings

                projects_dir = os.path.join(repo_path, "projects")
                if os.path.isdir(projects_dir):
                    for proj_id in sorted(os.listdir(projects_dir)):
                        proj_path = os.path.join(projects_dir, proj_id)
                        if not os.path.isdir(proj_path):
                            continue
                        proj_settings = read_settings(os.path.join(proj_path, "settings.json"))
                        if proj_settings:
                            repo_entry.setdefault("projects", {})[proj_id] = proj_settings

                if repo_entry:
                    org_entry.setdefault("repos", {})[repo_name] = repo_entry

        if org_entry:
            tree.setdefault("orgs", {})[org_name] = org_entry

    return tree
