import sqlite3
import json
from pathlib import Path
import requests
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from . import __init__ as _pkg  # noqa: F401 (keep package context)
from utils import get_api_base, get_basic_auth, get_authed_session


DB_PATH = Path.home() / ".rsportal" / "rsportal.db"


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = _conn()
    cur = conn.cursor()
    # tasks table
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS tasks (
        id TEXT PRIMARY KEY,
        project TEXT,
        title TEXT,
        task_id_link TEXT,
        assigner TEXT,
        assignee TEXT,
        category TEXT,
        status TEXT,
        urgency TEXT,
        deadline TEXT,
        objective TEXT,
        summary TEXT,
        documentation TEXT,
        credentials TEXT,
        pm_approved INTEGER DEFAULT 0,
        pm_reviewer TEXT,
        cto_approved INTEGER DEFAULT 0,
        cto_reviewer TEXT,
        created_at TEXT,
        updated_at TEXT,
        local_notes TEXT,
        synced INTEGER DEFAULT 0
    )
    """
    )

    # time entries
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS time_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id TEXT,
        user TEXT,
        start_time TEXT,
        end_time TEXT,
        notes TEXT,
        synced INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now'))
    )
    """
    )
    # comments
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id TEXT,
        author TEXT,
        comment TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        synced INTEGER DEFAULT 0
    )
    """
    )

    # auth table to optionally store username/password locally (per user's request)
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS auth (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT,
        email TEXT,
        active INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now'))
    )
    """
    )

    conn.commit()
    conn.close()


def get_saved_auth() -> Union[None, Dict[str, str]]:
    """Return active saved auth from sqlite or None."""
    conn: sqlite3.Connection = _conn()
    cur: sqlite3.Cursor = conn.cursor()

    cur.execute(
        "SELECT username, password FROM auth WHERE active = 1 ORDER BY id DESC LIMIT 1"
    )

    r: Union[None, sqlite3.Row] = cur.fetchone()

    conn.close()

    if not r:
        return None

    return {"username": r["username"], "password": r["password"]}


def save_auth(username: str, password: str, force: bool = False) -> bool:
    """Save credentials into sqlite. If an active auth exists and force is False, do not overwrite.

    Returns True when saved/activated or already active with same creds.
    Returns False when there is an active different auth and force is False.
    """
    base_url: str = get_api_base()
    auth_url: str = f"{base_url}/auth/check"

    resp = requests.get(auth_url, timeout=15, auth=(username, password))
    if not resp.status_code in (200, 204):
        return False

    existing: Union[None, Dict[str, str]] = get_saved_auth()

    if existing and not force:
        # if same creds, consider success; if different, do not overwrite by default
        if (
            existing.get("username") == username
            and existing.get("password") == password
        ):
            return True
        return False

    conn: sqlite3.Connection = _conn()
    cur: sqlite3.Cursor = conn.cursor()

    if existing:
        # mark others inactive
        cur.execute("UPDATE auth SET active = 0 WHERE active = 1")

    cur.execute(
        "INSERT INTO auth (username, password, active) VALUES (?, ?, 1)",
        (username, password),
    )

    conn.commit()
    conn.close()
    return True


def clear_auth() -> bool:
    """Deactivate any active auth. Returns True if any were deactivated."""
    conn: sqlite3.Connection = _conn()
    cur: sqlite3.Cursor = conn.cursor()
    cur.execute("SELECT COUNT(*) as c FROM auth WHERE active = 1")
    r: Union[None, sqlite3.Row] = cur.fetchone()
    if not r or r["c"] == 0:
        conn.close()
        return False
    cur.execute("UPDATE auth SET active = 0 WHERE active = 1")
    conn.commit()
    conn.close()
    return True


def upsert_time_entries(entries: List[Dict[str, Any]]):
    conn: sqlite3.Connection = _conn()
    cur: sqlite3.Cursor = conn.cursor()

    def _norm_field(v: Any) -> Any:
        # Normalize values so sqlite bindings accept them: primitives pass through;
        # dicts/lists are JSON-serialized to strings.
        if v is None:
            return None
        if isinstance(v, (str, int, float)):
            return v
        try:
            # sqlite does accept bytes, but we will store complex types as JSON strings
            return json.dumps(v)
        except Exception:
            return str(v)

    conn = _conn()
    cur = conn.cursor()

    for e in entries:
        eid = e.get("id")
        if not eid:
            continue
        cur.execute("SELECT id FROM time_entries WHERE id = ?", (eid,))
        exists = cur.fetchone()
        params = (
            eid,
            _norm_field(e.get("task_id")),
            _norm_field(e.get("user")),
            _norm_field(e.get("start_time")),
            _norm_field(e.get("end_time")),
            _norm_field(e.get("notes")),
            1 if e.get("synced") else 0,
        )
        if exists:
            cur.execute(
                """
            UPDATE time_entries SET task_id=?, user=?, start_time=?, end_time=?, notes=?, synced=?
            WHERE id=?
            """,
                params[1:] + (params[0],),
            )
        else:
            cur.execute(
                """
            INSERT INTO time_entries (id, task_id, user, start_time, end_time, notes, synced)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                params,
            )
    conn.commit()
    conn.close()


def upsert_tasks(tasks: List[Dict[str, Any]]):
    conn: sqlite3.Connection = _conn()
    cur: sqlite3.Cursor = conn.cursor()

    def _norm_field(v: Any) -> Any:
        # Normalize values so sqlite bindings accept them: primitives pass through;
        # dicts/lists are JSON-serialized to strings.
        if v is None:
            return None
        if isinstance(v, (str, int, float)):
            return v
        try:
            # sqlite does accept bytes, but we will store complex types as JSON strings
            return json.dumps(v)
        except Exception:
            return str(v)

    for t in tasks:
        tid = str(t.get("id") or t.get("task_id") or "")
        if not tid:
            continue
        cur.execute("SELECT id FROM tasks WHERE id = ?", (tid,))
        exists = cur.fetchone()
        params = (
            tid,
            _norm_field(t.get("project")),
            _norm_field(t.get("title")),
            _norm_field(t.get("task_id_link")),
            _norm_field(t.get("assigner")),
            _norm_field(t.get("assignee")),
            _norm_field(t.get("category")),
            _norm_field(t.get("status")),
            _norm_field(t.get("urgency")),
            _norm_field(t.get("deadline")),
            _norm_field(t.get("objective")),
            _norm_field(t.get("summary")),
            _norm_field(t.get("documentation") or {}),
            _norm_field(t.get("credentials")),
            1 if t.get("pm_approved") else 0,
            _norm_field(t.get("pm_reviewer")),
            1 if t.get("cto_approved") else 0,
            _norm_field(t.get("cto_reviewer")),
            _norm_field(t.get("created_at")),
            _norm_field(t.get("updated_at")),
            _norm_field(t.get("local_notes") or ""),
        )
        if exists:
            cur.execute(
                """
            UPDATE tasks SET project=?, title=?, task_id_link=?, assigner=?, assignee=?, category=?,
                status=?, urgency=?, deadline=?, objective=?, summary=?, documentation=?, credentials=?,
                pm_approved=?, pm_reviewer=?, cto_approved=?, cto_reviewer=?, created_at=?, updated_at=?, local_notes=?
            WHERE id=?
            """,
                params[1:] + (params[0],),
            )
        else:
            cur.execute(
                """
            INSERT INTO tasks (id, project, title, task_id_link, assigner, assignee, category, status,
                urgency, deadline, objective, summary, documentation, credentials, pm_approved, pm_reviewer,
                cto_approved, cto_reviewer, created_at, updated_at, local_notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                params,
            )
    conn.commit()
    conn.close()


def get_tasks(status: Optional[str] = None) -> List[Dict[str, Any]]:
    init_db()
    conn = _conn()
    cur = conn.cursor()
    if status and status.upper() != "ALL":
        cur.execute(
            "SELECT * FROM tasks WHERE status = ? ORDER BY updated_at DESC", (status,)
        )
    else:
        cur.execute("SELECT * FROM tasks ORDER BY updated_at DESC")
    rows = cur.fetchall()
    res = []
    for r in rows:
        d = dict(r)
        try:
            d["documentation"] = json.loads(d.get("documentation") or "{}")
        except Exception:
            d["documentation"] = {}
        res.append(d)
    conn.close()
    return res


def get_task(task_id: str) -> Optional[Dict[str, Any]]:
    conn = _conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    r = cur.fetchone()
    if not r:
        conn.close()
        return None
    d = dict(r)
    try:
        d["documentation"] = json.loads(d.get("documentation") or "{}")
    except Exception:
        d["documentation"] = {}
    conn.close()
    return d


def refresh_comments_from_remote() -> int:
    """Fetch comments from remote API and upsert into sqlite. Returns number of comments pulled."""
    # Placeholder implementation

    return 0


def refresh_documentation_from_remote() -> int:
    """Fetch documentation from remote API and upsert into sqlite. Returns number of documentations pulled."""
    # Placeholder implementation
    return 0


def refresh_time_entries_from_remote() -> int:
    """Fetch time entries from remote API and upsert into sqlite. Returns number of time entries pulled."""
    # Placeholder implementation
    url: str = f"{get_api_base()}/time/entries"
    try:
        saved: Union[None, Dict[str, str]] = get_saved_auth()
        if saved:
            resp = requests.get(
                url, timeout=30, auth=(saved.get("username"), saved.get("password"))
            )
            if resp.status_code == 401:
                return 0
            if resp.status_code == 403:
                return 0
        else:
            session = get_authed_session()
            if session is not None:
                resp = session.get(url, timeout=30)
            else:
                auth = get_basic_auth()
                resp = requests.get(url, timeout=30, auth=auth if all(auth) else None)

        if resp.status_code != 200:
            return 0
        remote_entries = resp.json()
    except Exception:
        return 0

    merged_time_entries = []
    for re in remote_entries:
        eid = re.get("id")
        if not eid:
            continue
        merged_time_entries.append(
            {
                "id": eid,
                "task_id": re.get("task"),
                "user": re.get("user"),
                "start_time": re.get("start_time"),
                "end_time": re.get("end_time"),
                "notes": re.get("notes"),
                "synced": True,
            }
        )

    upsert_time_entries(merged_time_entries)
    return len(merged_time_entries)


def refresh_tasks_from_remote() -> int:
    """Fetch tasks from remote API and upsert into sqlite. Returns number of tasks pulled."""
    base: str = get_api_base()
    url: str = f"{base}/tasks/assigned"

    try:
        # Prefer saved sqlite auth (GUI-managed) when available
        saved: Union[None, Dict[str, str]] = get_saved_auth()

        if saved:
            resp = requests.get(
                url, timeout=30, auth=(saved.get("username"), saved.get("password"))
            )
            if resp.status_code == 401:
                return 0
            if resp.status_code == 403:
                return 0
        else:
            session = get_authed_session()
            if session is not None:
                resp = session.get(url, timeout=30)
            else:
                auth = get_basic_auth()
                resp = requests.get(url, timeout=30, auth=auth if all(auth) else None)
        if resp.status_code != 200:
            return 0
        remote_tasks = resp.json()
    except Exception:
        return 0

    # Transform into the merged shape used by pull_cmd
    merged = []
    for rt in remote_tasks:
        tid = rt.get("id")
        if not tid:
            continue
        merged.append(
            {
                "id": tid,
                "project": rt.get("project"),
                "title": rt.get("title") or "",
                "task_id_link": rt.get("task_id_link"),
                "assigner": rt.get("assigner"),
                "assignee": rt.get("assignee"),
                "category": rt.get("category") or "GENERAL",
                "status": rt.get("status") or "TODO",
                "urgency": rt.get("urgency") or "MEDIUM",
                "deadline": rt.get("deadline"),
                "objective": rt.get("objective") or "",
                "summary": rt.get("summary"),
                "documentation": rt.get("documentation") or {},
                "credentials": "",
                "pm_approved": bool(rt.get("pm_approved")),
                "pm_reviewer": rt.get("pm_reviewer"),
                "cto_approved": bool(rt.get("cto_approved")),
                "cto_reviewer": rt.get("cto_reviewer"),
                "created_at": rt.get("created_at"),
                "updated_at": rt.get("updated_at"),
                "local_notes": "",
            }
        )

    upsert_tasks(merged)
    return len(merged)


def save_time_entry(
    task_id: str, start_time: str, end_time: Optional[str], notes: Optional[str] = None
) -> int:
    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO time_entries (task_id, start_time, end_time, notes, synced) VALUES (?, ?, ?, ?, 0)",
        (task_id, start_time, end_time, notes or ""),
    )
    conn.commit()
    rowid = cur.lastrowid
    conn.close()
    return rowid


def get_time_entries(task_id: str) -> List[Dict[str, Any]]:
    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM time_entries WHERE task_id = ? ORDER BY start_time DESC",
        (task_id,),
    )
    rows = cur.fetchall()
    res = [dict(r) for r in rows]
    conn.close()
    return res


def stop_running_entries_and_get(task_id: Optional[str] = None) -> List[Dict[str, Any]]:
    # Set end_time to now for entries with null end_time
    conn = _conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat() + "Z"
    if task_id:
        cur.execute(
            "UPDATE time_entries SET end_time = ? WHERE task_id = ? AND end_time IS NULL",
            (now, task_id),
        )
    else:
        cur.execute(
            "UPDATE time_entries SET end_time = ? WHERE end_time IS NULL", (now,)
        )
    conn.commit()
    # return affected
    cur.execute("SELECT * FROM time_entries WHERE end_time = ?", (now,))
    rows = cur.fetchall()
    res = [dict(r) for r in rows]
    conn.close()
    return res
