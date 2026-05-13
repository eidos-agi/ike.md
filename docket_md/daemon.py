"""docket-daemon — queue-driven watcher for Claude Code session JSONL files.

Instead of scanning all JONLs globally, the daemon reads jobs from a queue file
populated by a Claude Code SessionStart hook.  Only sessions in docket-managed
projects are watched.
"""

import json
import logging
import os
import signal
import sys
import time
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler

# ── Configuration ────────────────────────────────────────────────────────────

CONFIG_DIR = os.path.expanduser("~/.config/docket")
STATE_FILE = os.path.join(CONFIG_DIR, "daemon-state.json")
PID_FILE = os.path.join(CONFIG_DIR, "docket-daemon.pid")
LOG_FILE = os.path.join(CONFIG_DIR, "docket-daemon.log")
QUEUE_FILE = os.path.join(CONFIG_DIR, "daemon-queue.jsonl")
SETTINGS_FILE = os.path.expanduser("~/.claude/settings.json")
POLL_INTERVAL = 30  # seconds

logger = logging.getLogger("docket-daemon")

# ── Graceful import of session helpers ───────────────────────────────────────

try:
    from .files import add_session, add_session_event, load_sessions
    HAS_SESSION_HELPERS = True
except ImportError:
    HAS_SESSION_HELPERS = False
    add_session = None  # type: ignore[assignment]
    add_session_event = None  # type: ignore[assignment]
    load_sessions = None  # type: ignore[assignment]

# ── State management ─────────────────────────────────────────────────────────

_shutdown = False


def load_state() -> dict:
    """Load daemon state from ~/.config/docket/daemon-state.json."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                state = json.load(f)
            # Migrate old format: rename "offsets" to "watches" if needed
            if "offsets" in state and "watches" not in state:
                state["watches"] = {}
                del state["offsets"]
            return state
        except (json.JSONDecodeError, OSError):
            logger.warning("Corrupt state file, starting fresh")
    return {"watches": {}, "ingested": []}


def save_state(state: dict) -> None:
    """Save daemon state."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, STATE_FILE)


# ── Detection ────────────────────────────────────────────────────────────────

def _is_plan_approval(obj: dict) -> dict | None:
    """Check if a JSONL entry is a plan approval event.

    Returns {plan_content, plan_path, session_id} or None.
    """
    if obj.get("type") != "user":
        return None

    message = obj.get("message", {})
    content_list = message.get("content", [])
    tool_use_result = obj.get("toolUseResult", {})

    # Must have toolUseResult with plan data
    if not tool_use_result or not isinstance(tool_use_result, dict):
        return None

    plan_content = tool_use_result.get("plan")
    plan_path = tool_use_result.get("filePath")

    if not plan_content or not plan_path:
        return None

    # Check that the content has the "approved your plan" signal
    approved = False
    if isinstance(content_list, list):
        for item in content_list:
            if isinstance(item, dict) and item.get("type") == "tool_result":
                text = item.get("content", "")
                if isinstance(text, str) and "approved your plan" in text.lower():
                    approved = True
                    break
                # content might be a list of dicts with text
                if isinstance(text, list):
                    for sub in text:
                        if isinstance(sub, dict) and "approved your plan" in sub.get("text", "").lower():
                            approved = True
                            break

    if not approved:
        return None

    return {
        "plan_content": plan_content,
        "plan_path": plan_path,
        "session_id": obj.get("sessionId", "unknown"),
    }


def _extract_title(plan_content: str) -> str:
    """Extract plan title from markdown content (first # heading)."""
    for line in plan_content.split("\n"):
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return "Untitled Plan"


def _ingest_plan(project_root: str, approval: dict) -> str | None:
    """Create a plan file in .docket/plans/ from an approval event.

    Returns the plan ID if created, None if duplicate.
    """
    from .config import DIRECTORIES, DOCKET_DIR
    from .files import (
        _next_id,
        _slugify,
        list_plans,
        write_markdown,
    )
    from .security import safe_path

    plan_content = approval["plan_content"]
    title = _extract_title(plan_content)

    # Dedup: check if a plan with the same title exists
    existing = list_plans(project_root)
    for p in existing:
        if p.frontmatter.get("title", "").lower() == title.lower():
            logger.info("Duplicate plan skipped: %s", title)
            return None

    # Generate next ID
    existing_ids = [p.frontmatter["id"] for p in existing if "id" in p.frontmatter]
    plan_id = _next_id("PLAN", existing_ids)

    slug = _slugify(title)
    file_path = safe_path(project_root, DOCKET_DIR, DIRECTORIES["PLANS"], f"{plan_id} - {slug}.md")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    frontmatter = {
        "id": plan_id,
        "title": title,
        "status": "approved",
        "created": now,
        "source": "daemon",
        "session_id": approval["session_id"],
    }

    # Strip the title heading from content since it's in frontmatter
    body_lines = []
    found_title = False
    for line in plan_content.split("\n"):
        if not found_title and line.strip().startswith("# "):
            found_title = True
            continue
        body_lines.append(line)
    body = "\n".join(body_lines).strip()

    # Ensure .docket/plans/ exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    write_markdown(file_path, frontmatter, body)

    logger.info("Ingested plan %s: %s -> %s", plan_id, title, file_path)
    return plan_id


# ── Install hook ─────────────────────────────────────────────────────────────

def install() -> None:
    """Install the SessionStart hook into ~/.claude/settings.json."""
    settings_dir = os.path.dirname(SETTINGS_FILE)
    os.makedirs(settings_dir, exist_ok=True)

    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE) as f:
            settings = json.load(f)
    else:
        settings = {"hooks": {}}

    if "hooks" not in settings:
        settings["hooks"] = {}

    hook_command = (
        "jq -c '{type:\"watch_session\",session_id:.session_id,"
        "jsonl:.transcript_path,cwd:.cwd}' >> ~/.config/docket/daemon-queue.jsonl"
    )

    docket_hook = {
        "type": "command",
        "command": hook_command,
        "timeout": 5,
    }

    session_start_hooks = settings["hooks"].get("SessionStart", [])

    # Check if docket hook already exists (avoid duplicates)
    for entry in session_start_hooks:
        hooks_list = entry.get("hooks", [])
        for h in hooks_list:
            if "daemon-queue.jsonl" in h.get("command", ""):
                print("docket SessionStart hook already installed.")
                return

    # Add the docket hook entry
    session_start_hooks.append({
        "matcher": "",
        "hooks": [docket_hook],
    })
    settings["hooks"]["SessionStart"] = session_start_hooks

    # Atomic write
    tmp = SETTINGS_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(settings, f, indent=2)
        f.write("\n")
    os.replace(tmp, SETTINGS_FILE)

    print("Hook installed. Restart Claude Code or open /hooks to activate.")


# ── Queue processing ─────────────────────────────────────────────────────────

def process_queue(state: dict) -> dict:
    """Read QUEUE_FILE, register new sessions, add to watch list."""
    if not os.path.exists(QUEUE_FILE):
        return state

    watches = state.get("watches", {})

    try:
        with open(QUEUE_FILE) as f:
            lines = f.readlines()
    except OSError as e:
        logger.warning("Failed to read queue file: %s", e)
        return state

    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            job = json.loads(line)
        except json.JSONDecodeError:
            logger.warning("Malformed queue entry: %s", line[:80])
            continue

        if job.get("type") != "watch_session":
            logger.debug("Unknown job type: %s", job.get("type"))
            continue

        cwd = job.get("cwd", "")
        jsonl = job.get("jsonl", "")
        session_id = job.get("session_id", "")

        if not cwd or not jsonl or not session_id:
            logger.warning("Incomplete job, skipping: %s", line[:80])
            continue

        # Check if cwd has .docket/docket.json (skip if not an docket project)
        docket_json_path = os.path.join(cwd, ".docket", "docket.json")
        if not os.path.exists(docket_json_path):
            logger.debug("No .docket/docket.json in %s, skipping", cwd)
            continue

        # Load project config to get project_id and name
        try:
            with open(docket_json_path) as f:
                docket_config = json.load(f)
            project_id = docket_config.get("id", "unknown")
            project_name = docket_config.get("project", os.path.basename(cwd))
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to read docket.json in %s: %s", cwd, e)
            continue

        # Register session in .docket/sessions.json
        if HAS_SESSION_HELPERS and add_session is not None:
            try:
                add_session(cwd, session_id, jsonl, project_id)
            except Exception as e:
                logger.warning("Failed to register session %s: %s", session_id, e)

        # Add to watches (skip if already watching this jsonl)
        if jsonl not in watches:
            # Watermark at current file size — only process NEW events
            try:
                offset = os.path.getsize(jsonl) if os.path.exists(jsonl) else 0
            except OSError:
                offset = 0

            watches[jsonl] = {
                "project_root": cwd,
                "project_id": project_id,
                "session_id": session_id,
                "offset": offset,
            }
            logger.info("Watching session %s for project %s", session_id, project_name)

    # Truncate queue file after processing
    try:
        with open(QUEUE_FILE, "w") as f:
            pass  # truncate to zero
    except OSError as e:
        logger.warning("Failed to truncate queue file: %s", e)

    state["watches"] = watches
    return state


# ── File watching ────────────────────────────────────────────────────────────

def watch_files(state: dict) -> dict:
    """Check watched JSONL files for new plan approvals."""
    watches = state.get("watches", {})
    ingested = state.get("ingested", [])
    to_remove = []

    for jsonl_path, info in watches.items():
        if not os.path.exists(jsonl_path):
            logger.warning("Watched file gone: %s", jsonl_path)
            to_remove.append(jsonl_path)
            continue

        try:
            file_size = os.path.getsize(jsonl_path)
        except OSError:
            continue

        prev_offset = info.get("offset", 0)
        if file_size <= prev_offset:
            continue

        project_root = info["project_root"]
        session_id = info["session_id"]

        try:
            with open(jsonl_path, "r", errors="replace") as f:
                f.seek(prev_offset)
                new_data = f.read()
                new_offset = f.tell()
        except OSError as e:
            logger.warning("Failed to read %s: %s", jsonl_path, e)
            continue

        for line in new_data.split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            approval = _is_plan_approval(obj)
            if not approval:
                continue

            # Dedup key: session_id + plan title
            title = _extract_title(approval["plan_content"])
            dedup_key = f"{approval['session_id']}:{title}"
            if dedup_key in ingested:
                continue

            # Check .docket exists in project
            docket_dir = os.path.join(project_root, ".docket")
            if not os.path.isdir(docket_dir):
                logger.debug("No .docket directory in %s, skipping", project_root)
                continue

            plan_id = _ingest_plan(project_root, approval)
            if plan_id:
                ingested.append(dedup_key)

                # Record event in sessions.json
                if HAS_SESSION_HELPERS and add_session_event is not None:
                    try:
                        event = {
                            "type": "plan_approved",
                            "plan_id": plan_id,
                            "at": datetime.now(timezone.utc).isoformat(),
                        }
                        add_session_event(project_root, session_id, event)
                    except Exception as e:
                        logger.warning("Failed to record session event: %s", e)

                # Keep ingested list bounded
                if len(ingested) > 1000:
                    ingested = ingested[-500:]

        info["offset"] = new_offset

    for path in to_remove:
        del watches[path]

    state["watches"] = watches
    state["ingested"] = ingested
    return state


# ── Signal handling ──────────────────────────────────────────────────────────

def _handle_signal(signum: int, frame: object) -> None:
    global _shutdown
    logger.info("Received signal %d, shutting down", signum)
    _shutdown = True


# ── Entry point ──────────────────────────────────────────────────────────────

def main() -> None:
    """Entry point: setup logging, PID file, signal handlers, polling loop."""
    global _shutdown

    # Subcommand handling
    if len(sys.argv) > 1:
        if sys.argv[1] == "install":
            install()
            sys.exit(0)
        elif sys.argv[1] == "status":
            state = load_state()
            watches = state.get("watches", {})
            queue_depth = 0
            if os.path.exists(QUEUE_FILE):
                try:
                    with open(QUEUE_FILE) as f:
                        queue_depth = sum(1 for line in f if line.strip())
                except OSError:
                    pass
            print(f"Watches: {len(watches)}")
            for jsonl, info in watches.items():
                print(f"  {info['session_id']}  {info['project_root']}  offset={info['offset']}")
            print(f"Queue depth: {queue_depth}")
            print(f"Ingested: {len(state.get('ingested', []))}")
            sys.exit(0)

    os.makedirs(CONFIG_DIR, exist_ok=True)

    # Logging
    handler = RotatingFileHandler(LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    # Also log to stderr for interactive use
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(stderr_handler)

    # PID file
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    logger.info("docket-daemon started (pid=%d, poll=%ds)", os.getpid(), POLL_INTERVAL)

    state = load_state()

    try:
        while not _shutdown:
            try:
                state = process_queue(state)
                state = watch_files(state)
                save_state(state)
            except Exception:
                logger.exception("Error during poll cycle")
            time.sleep(POLL_INTERVAL)
    finally:
        logger.info("docket-daemon shutting down")
        try:
            os.remove(PID_FILE)
        except OSError:
            pass


if __name__ == "__main__":
    main()
