"""Project configuration and GUID registry."""

import json
import os
import uuid
from dataclasses import dataclass
from datetime import date

DOCKET_DIR = ".docket"
CONFIG_FILENAME = "docket.json"

DIRECTORIES = {
    "TASKS": "tasks",
    "COMPLETED": "completed",
    "ARCHIVE": "archive",
    "MILESTONES": "milestones",
    "DOCUMENTS": "documents",
    "GRAPH": "graph",
    "PLANS": "plans",
}

# In-memory GUID → path registry. Per-process, no disk state.
_guid_to_path: dict[str, str] = {}


@dataclass
class DocketConfig:
    id: str
    version: str
    project: str
    created: str
    docket_path: str


def load_config(dir_path: str) -> DocketConfig | None:
    config_path = os.path.join(dir_path, DOCKET_DIR, CONFIG_FILENAME)
    if not os.path.exists(config_path):
        return None
    try:
        with open(config_path) as f:
            data = json.load(f)
        return DocketConfig(**data)
    except Exception:
        return None


def save_config(dir_path: str, config: DocketConfig) -> None:
    docket_dir = os.path.join(dir_path, DOCKET_DIR)
    os.makedirs(docket_dir, exist_ok=True)
    with open(os.path.join(docket_dir, CONFIG_FILENAME), "w") as f:
        json.dump(
            {
                "id": config.id,
                "version": config.version,
                "project": config.project,
                "created": config.created,
                "docket_path": config.docket_path,
            },
            f,
            indent=2,
        )
        f.write("\n")


def init_project(target_dir: str, project_name: str | None = None) -> DocketConfig:
    docket_dir = os.path.join(target_dir, DOCKET_DIR)
    for d in DIRECTORIES.values():
        os.makedirs(os.path.join(docket_dir, d), exist_ok=True)

    existing = load_config(target_dir)
    if existing:
        return existing

    config = DocketConfig(
        id=str(uuid.uuid4()),
        version="0.1.0",
        project=project_name or os.path.basename(os.path.abspath(target_dir)),
        created=date.today().isoformat(),
        docket_path=DOCKET_DIR,
    )
    save_config(target_dir, config)
    return config


def register_project(project_path: str) -> dict[str, str]:
    abs_path = os.path.abspath(project_path)
    config = load_config(abs_path)
    if not config:
        raise ValueError(
            f"No docket.json at {abs_path}. Call project_init first to initialize docket.md in this directory."
        )
    _guid_to_path[config.id] = abs_path
    return {"id": config.id, "project": config.project}


def resolve_project(project_id: object) -> str:
    if not project_id or not isinstance(project_id, str):
        raise ValueError(
            "Missing required parameter: project_id. "
            "Call project_set with the project path to register it and get its GUID. "
            "Or call project_init to create a new docket.md project."
        )
    project_path = _guid_to_path.get(project_id)
    if not project_path:
        raise ValueError(
            f"Unknown project_id '{project_id}'. This project hasn't been registered in this session. "
            "Call project_set with the project path to register it. "
            "The project_id is the 'id' field in the project's docket.json."
        )
    return project_path


def list_registered() -> list[dict[str, str]]:
    return [{"id": id, "path": p} for id, p in _guid_to_path.items()]
