"""Optional Wrike sync hook for docket.md.

Fires on project_set (find/create Wrike task), bookmark (add comment),
and task_complete (mark Wrike task done). Uses Wrike REST API directly
with WRDOCKET_ACCESS_TOKEN from environment. No dependency on wrike-mcp.

Graceful degradation: if httpx is not installed, WRDOCKET_ACCESS_TOKEN is
not set, or wrike.enabled is false — returns None and does nothing.
"""

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

WRDOCKET_API = "https://www.wrike.com/api/v4"


class WrikeHook:
    """Thin Wrike API wrapper for docket.md hook events."""

    def __init__(self, access_token: str):
        self._token = access_token
        try:
            import httpx
            self._http = httpx.Client(timeout=15)
        except ImportError:
            raise ImportError("httpx is required for Wrdocket hook. Install with: pip install httpx")

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    def _get(self, path: str, params: dict | None = None) -> Any:
        resp = self._http.get(f"{WRDOCKET_API}{path}", headers=self._headers(), params=params)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, data: dict | None = None) -> Any:
        resp = self._http.post(f"{WRDOCKET_API}{path}", headers=self._headers(), json=data)
        resp.raise_for_status()
        return resp.json()

    def _put(self, path: str, data: dict | None = None) -> Any:
        resp = self._http.put(f"{WRDOCKET_API}{path}", headers=self._headers(), json=data)
        resp.raise_for_status()
        return resp.json()

    # -- Hook events ----------------------------------------------------------

    def on_project_set(
        self,
        project_name: str,
        folder_id: str,
    ) -> str | None:
        """Search Wrike for a task matching *project_name* in *folder_id*.
        If found, return its task ID. If not, create one and return the ID.
        """
        # Search in folder
        try:
            result = self._get(
                f"/folders/{folder_id}/tasks",
                params={"title": project_name, "status": "Active"},
            )
            tasks = result.get("data", [])
            for t in tasks:
                if t.get("title", "").lower() == project_name.lower():
                    logger.info(f"Wrike: found existing task {t['id']} for '{project_name}'")
                    return t["id"]
        except Exception as e:
            logger.warning(f"Wrike search failed: {e}")

        # Create new task
        try:
            result = self._post(
                f"/folders/{folder_id}/tasks",
                data={
                    "title": f"[docket] {project_name}",
                    "description": f"Tracked by docket.md. Source: local project.",
                    "status": "Active",
                },
            )
            tasks = result.get("data", [])
            if tasks:
                task_id = tasks[0]["id"]
                logger.info(f"Wrike: created task {task_id} for '{project_name}'")
                return task_id
        except Exception as e:
            logger.warning(f"Wrike task creation failed: {e}")

        return None

    def on_bookmark(self, wrike_task_id: str, note: str) -> None:
        """Post a comment on the Wrike task."""
        try:
            self._post(
                f"/tasks/{wrike_task_id}/comments",
                data={"text": note, "plainText": True},
            )
            logger.info(f"Wrike: posted bookmark to {wrike_task_id}")
        except Exception as e:
            logger.warning(f"Wrike comment failed: {e}")

    def on_complete(self, wrike_task_id: str) -> None:
        """Mark the Wrike task as Completed."""
        try:
            self._put(
                f"/tasks/{wrike_task_id}",
                data={"status": "Completed"},
            )
            logger.info(f"Wrike: marked {wrike_task_id} as Completed")
        except Exception as e:
            logger.warning(f"Wrike status update failed: {e}")


def get_hook(settings: dict) -> WrikeHook | None:
    """Return a WrikeHook if wrike.enabled=true and WRDOCKET_ACCESS_TOKEN is set.
    Returns None (silently) if conditions aren't met.
    """
    wrike_cfg = settings.get("wrike", {})
    if not wrike_cfg.get("enabled"):
        return None

    token = os.getenv("WRDOCKET_ACCESS_TOKEN")
    if not token:
        logger.debug("wrike.enabled=true but WRDOCKET_ACCESS_TOKEN not set — skipping hook")
        return None

    try:
        return WrikeHook(token)
    except ImportError:
        logger.debug("httpx not installed — Wrdocket hook disabled")
        return None
