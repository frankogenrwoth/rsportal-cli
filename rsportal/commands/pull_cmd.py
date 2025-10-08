import os
import json
from typing import List, Dict, Any
from utils import require_auth
from rsportal.storage import load_tasks, save_tasks, ensure_storage_migration
from utils import get_api_base, get_basic_auth, get_authed_session

try:
    import requests

    HAS_REQUESTS = True
except Exception:
    HAS_REQUESTS = False


def handle(args):
    # Require auth for pulling
    require_auth()
    ensure_storage_migration()

    if getattr(args, "pull_cmd", None) == "tasks" or getattr(args, "tasks", False):
        pull_tasks()
        return

    # Default: show help
    show_help()


def pull_tasks():
    if not HAS_REQUESTS:
        print("\nError: 'requests' not installed. Install with: pip install requests\n")
        return

    base = get_api_base()
    url = f"{base}/tasks/assigned"

    try:
        session = get_authed_session()
        if session is not None:
            resp = session.get(url, timeout=30)
        else:
            # Fallback: unauthenticated or basic (if server accepts)
            auth = get_basic_auth()
            resp = requests.get(url, timeout=30, auth=auth if all(auth) else None)
        if resp.status_code != 200:
            print(f"\nFailed to pull tasks: HTTP {resp.status_code}\n")
            return
        remote_tasks = resp.json()
    except Exception as e:
        print(f"\nFailed to pull tasks: {e}\n")
        return

    # Preserve local_notes while updating remote fields
    local_tasks = load_tasks()
    id_to_local = {t.get("id"): t for t in local_tasks if t.get("id")}
    merged: List[Dict[str, Any]] = []

    for rt in remote_tasks:
        tid = rt.get("id") or rt.get("task_id")
        if not tid:
            continue
        lt = id_to_local.get(tid, {})
        merged.append(
            {
                "id": tid,
                "project": rt.get("project"),
                "title": rt.get("title") or lt.get("title", ""),
                "task_id_link": rt.get("task_id_link") or lt.get("task_id_link"),
                "assigner": rt.get("assigner"),
                "assignee": rt.get("assignee"),
                "category": rt.get("category") or "GENERAL",
                "status": rt.get("status") or "TODO",
                "urgency": rt.get("urgency") or "MEDIUM",
                "deadline": rt.get("deadline"),
                "objective": rt.get("objective") or lt.get("objective", ""),
                "summary": rt.get("summary") or lt.get("summary"),
                "documentation": rt.get("documentation") or lt.get("documentation"),
                "credentials": lt.get("credentials") if lt.get("credentials") else "",
                "pm_approved": bool(rt.get("pm_approved")),
                "pm_reviewer": rt.get("pm_reviewer"),
                "cto_approved": bool(rt.get("cto_approved")),
                "cto_reviewer": rt.get("cto_reviewer"),
                "created_at": rt.get("created_at") or lt.get("created_at"),
                "updated_at": rt.get("updated_at") or lt.get("updated_at"),
                # local-only notes
                "local_notes": lt.get("local_notes", ""),
            }
        )

    save_tasks(merged)
    print(f"\nPulled {len(merged)} tasks.\n")


def show_help():
    print(
        """
RSportal Pull Commands

Usage:
  rsportal pull tasks       # Pull assigned tasks from server
  rsportal pull --tasks

Configuration:
  Set RSPortal API base URL via env var RSPORTAL_API_BASE
        """
    )
