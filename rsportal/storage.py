import json
from pathlib import Path
from typing import Any, Dict, List, Optional


BASE_DIR = Path.home() / ".rsportal"
BASE_DIR.mkdir(parents=True, exist_ok=True)

AUTH_FILE = BASE_DIR / "auth.json"
TASKS_FILE = BASE_DIR / "tasks.json"
TIME_FILE = BASE_DIR / "time.json"
SYNC_LOG_FILE = BASE_DIR / "sync_log.json"
VERSION_FILE = BASE_DIR / ".version.json"


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2))


# Auth
def load_auth() -> Dict[str, Any]:
    return _read_json(AUTH_FILE, {})


def save_auth(data: Dict[str, Any]) -> None:
    _write_json(AUTH_FILE, data)


# Tasks
def load_tasks() -> List[Dict[str, Any]]:
    return _read_json(TASKS_FILE, [])


def save_tasks(tasks: List[Dict[str, Any]]) -> None:
    _write_json(TASKS_FILE, tasks)


# Time
def load_time() -> Dict[str, List[Dict[str, Any]]]:
    return _read_json(TIME_FILE, {})


def save_time(time_data: Dict[str, List[Dict[str, Any]]]) -> None:
    _write_json(TIME_FILE, time_data)


# Sync log
def load_sync_log() -> Dict[str, Any]:
    return _read_json(
        SYNC_LOG_FILE, {"last_sync": None, "synced_entries": [], "failed_entries": []}
    )


def save_sync_log(sync_log: Dict[str, Any]) -> None:
    _write_json(SYNC_LOG_FILE, sync_log)


# ---------------- Migration -----------------
STORAGE_VERSION = 1


def _read_version() -> int:
    data = _read_json(VERSION_FILE, {})
    return int(data.get("version", 0))


def _write_version(version: int) -> None:
    _write_json(VERSION_FILE, {"version": version})


def ensure_storage_migration() -> None:
    """Migrate local storage files to the latest schema.

    - tasks.json: ensure 'objective' exists; migrate legacy 'description' to 'objective' if needed;
      ensure 'local_notes' exists.
    - time.json: rename 'start'/'stop' to 'start_time'/'end_time'.
    """
    current = _read_version()
    if current >= STORAGE_VERSION:
        return

    # Migrate tasks.json
    tasks = load_tasks()
    migrated_tasks = []
    changed = False
    if isinstance(tasks, list):
        for t in tasks:
            if not isinstance(t, dict):
                continue
            obj = dict(t)
            # description (legacy) -> objective if objective missing/empty
            legacy_desc = (obj.get("description") or "").strip()
            objective = (obj.get("objective") or "").strip()
            if legacy_desc and not objective:
                obj["objective"] = legacy_desc
                changed = True
            # ensure local_notes exists
            if "local_notes" not in obj:
                obj["local_notes"] = ""
                changed = True
            migrated_tasks.append(obj)
    if changed:
        save_tasks(migrated_tasks)

    # Migrate time.json
    time_data = load_time()
    td_changed = False
    if isinstance(time_data, dict):
        for task_id, entries in list(time_data.items()):
            if not isinstance(entries, list):
                continue
            for e in entries:
                if not isinstance(e, dict):
                    continue
                if "start" in e and "start_time" not in e:
                    e["start_time"] = e.pop("start")
                    td_changed = True
                if "stop" in e and "end_time" not in e:
                    e["end_time"] = e.pop("stop")
                    td_changed = True
    if td_changed:
        save_time(time_data)

    _write_version(STORAGE_VERSION)
