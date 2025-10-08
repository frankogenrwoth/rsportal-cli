from utils import require_auth
from rsportal.storage import load_tasks, save_tasks
from rsportal.editor import open_editor, parse_title_and_description
from datetime import datetime


def handle(args):
    # Require authentication for task operations
    require_auth()

    # Subcommands
    if getattr(args, "tasks_cmd", None) == "list":
        do_list(
            urgency=getattr(args, "urgency", None),
            due_before=getattr(args, "due_before", None),
            due_after=getattr(args, "due_after", None),
        )
        return
    if getattr(args, "tasks_cmd", None) == "review":
        do_review(
            getattr(args, "task_id", None),
            getattr(args, "pm", False),
            getattr(args, "cto", False),
        )
        return
    # Disallow local mutation commands (pull from API instead)
    if getattr(args, "tasks_cmd", None) == "edit":
        do_edit(getattr(args, "task_id", None))
        return

    # Flags (backward compatibility)
    if getattr(args, "list", False):
        do_list(
            urgency=getattr(args, "urgency", None),
            due_before=getattr(args, "due_before", None),
            due_after=getattr(args, "due_after", None),
        )
        return
    # Back-compat flags are ignored for add/close/reopen/remove
    if getattr(args, "edit", False):
        do_edit(getattr(args, "task_id", None))
        return

    # Default: list tasks
    do_list()


def do_list(urgency=None, due_before=None, due_after=None):
    tasks = load_tasks()
    # Filtering
    if urgency:
        tasks = [t for t in tasks if (t.get("urgency") or "").upper() == urgency]

    def parse_date(s):
        try:
            return datetime.fromisoformat(s).date()
        except Exception:
            return None

    if due_before:
        cutoff = parse_date(due_before)
        if cutoff:
            tasks = [
                t
                for t in tasks
                if t.get("deadline")
                and parse_date(t.get("deadline"))
                and parse_date(t.get("deadline")) <= cutoff
            ]
    if due_after:
        start = parse_date(due_after)
        if start:
            tasks = [
                t
                for t in tasks
                if t.get("deadline")
                and parse_date(t.get("deadline"))
                and parse_date(t.get("deadline")) >= start
            ]
    print("\nTasks")
    print("=====")
    if not tasks:
        print("No tasks found. Use 'rsportal pull tasks' to fetch from server.\n")
        return
    for t in tasks:
        print(
            f"{t.get('id','(no-id)')}: {t.get('title','')} "
            f"[{(t.get('status') or 'TODO').upper()}] "
            f"{(t.get('urgency') or 'MEDIUM').title()} "
            f"{('due ' + t.get('deadline')) if t.get('deadline') else ''}"
        )
    print()


def do_review(task_id, pm, cto):
    if not task_id:
        print("\nError: Task ID is required (-i/--task-id).\n")
        return
    if pm and cto:
        print("\nError: Choose only one of --pm or --cto.\n")
        return
    if not pm and not cto:
        print("\nSpecify --pm or --cto to request review.\n")
        return
    # Update status locally for immediate feedback; remote update via API
    tasks = load_tasks()
    target = next((t for t in tasks if t.get("id") == task_id), None)
    if not target:
        print(f"\nTask '{task_id}' not found.\n")
        return
    new_status = "PM_REVIEW" if pm else "CTO_REVIEW"
    target["status"] = new_status
    save_tasks(tasks)
    print(f"\nMarked task {task_id} for {new_status}. Syncing to server...\n")
    # Defer to API call (in separate function)
    try_request_review(task_id, new_status)


def try_request_review(task_id, new_status):
    try:
        import os, requests

        base = os.environ.get("RSPORTAL_API_BASE", "https://api.example.com").rstrip(
            "/"
        )
        url = f"{base}/tasks/{task_id}/status"
        payload = {"status": new_status}
        # TODO: add auth headers if required
        resp = requests.post(url, json=payload, timeout=30)
        if resp.status_code in (200, 204):
            print("Server updated successfully.\n")
        else:
            print(f"Server update failed: HTTP {resp.status_code}\n")
    except Exception as e:
        print(f"Server update failed: {e}\n")


def do_add(title, task_id=None):
    print(
        "\nAdding tasks locally is disabled. Use 'rsportal pull tasks' to sync assigned tasks.\n"
    )


def do_update_status(task_id, status):
    print(
        "\nUpdating task status locally is disabled. Status is managed by the server.\n"
    )


def do_remove(task_id):
    print("\nRemoving tasks locally is disabled.\n")


def do_edit(task_id):
    if not task_id:
        print("\nError: Task ID is required (-i/--task-id).\n")
        return
    tasks = load_tasks()
    target = next((t for t in tasks if t.get("id") == task_id), None)
    if not target:
        print(f"\nTask '{task_id}' not found.\n")
        return
    # Title is provided by server (read-only); objective + local notes are editable.
    initial = (
        f"{target.get('title','')}\n\n"
        f"Objective:\n{target.get('objective','')}\n\n"
        f"Local Notes:\n{target.get('local_notes','')}\n"
    )
    content = open_editor(initial)
    # Parse by sections: after first line, expect 'Objective:' and 'Local Notes:' blocks
    lines = content.splitlines()
    obj_text = []
    notes_text = []
    section = None
    for line in lines[1:]:
        if line.strip().lower() == "objective:":
            section = "objective"
            continue
        if line.strip().lower() == "local notes:":
            section = "local_notes"
            continue
        if section == "objective":
            obj_text.append(line)
        elif section == "local_notes":
            notes_text.append(line)
    target["objective"] = "\n".join(obj_text).strip()
    target["local_notes"] = "\n".join(notes_text).strip()
    save_tasks(tasks)
    print(f"\nUpdated task {task_id}.\n")
