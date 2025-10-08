# rsportal/commands/log_cmd.py
from pathlib import Path
from datetime import datetime
from utils import require_auth
from rsportal.storage import load_time, load_tasks


TIME_FILE = Path.home() / ".rsportal" / "time.json"
TIME_FILE.parent.mkdir(parents=True, exist_ok=True)


def handle(args):
    # Require authentication
    require_auth()

    # Subcommands
    if getattr(args, "log_cmd", None) == "show":
        do_show(getattr(args, "task_id", None))
        return
    if getattr(args, "log_cmd", None) == "summary":
        do_summary(getattr(args, "task_id", None))
        return

    # Flags (backward compatibility)
    if getattr(args, "show", False):
        do_show(getattr(args, "task_id", None))
        return
    if getattr(args, "summary", False):
        do_summary(getattr(args, "task_id", None))
        return

    # Default: show summary
    do_summary(getattr(args, "task_id", None))


def load_json_time():
    return load_time()


def load_json_tasks():
    return load_tasks()


def do_show(task_id=None):
    time_data = load_json_time() or {}
    tasks = load_json_tasks() or []

    print("\nTime Log")
    print("========")

    if not time_data:
        print("No time entries found.\n")
        return

    if task_id:
        entries = time_data.get(task_id, [])
        if not entries:
            print(f"No entries for task '{task_id}'.\n")
            return
        print(f"Task: {task_id}")
        print("-" * (len(task_id) + 6))
        for i, e in enumerate(entries, 1):
            s = e.get("start_time") or e.get("start")
            eend = e.get("end_time") or e.get("stop")
            print(f"{i}. {s} -> {eend or 'RUNNING'}")
        print()
        return

    # Show all tasks entries
    for tid, entries in time_data.items():
        print(f"Task: {tid} ({len(entries)} entries)")
        for i, e in enumerate(entries, 1):
            s = e.get("start_time") or e.get("start")
            eend = e.get("end_time") or e.get("stop")
            print(f"  {i}. {s} -> {eend or 'RUNNING'}")
        print()


def do_summary(task_id=None):
    time_data = load_json_time() or {}
    tasks = load_json_tasks() or []

    def duration_seconds(start_str, stop_str=None):
        try:
            start = datetime.fromisoformat(start_str)
            stop = datetime.fromisoformat(stop_str) if stop_str else datetime.now()
            return int((stop - start).total_seconds())
        except Exception:
            return 0

    def format_seconds(total):
        hours = total // 3600
        minutes = (total % 3600) // 60
        seconds = total % 60
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        if minutes > 0:
            return f"{minutes}m {seconds}s"
        return f"{seconds}s"

    print("\nTime Summary")
    print("===========")

    if task_id:
        entries = time_data.get(task_id, [])
        total = sum(duration_seconds(e.get("start"), e.get("stop")) for e in entries)
        print(
            f"Task {task_id}: {format_seconds(total)} across {len(entries)} entries\n"
        )
        return

    if not time_data:
        print("No time entries found.\n")
        return

    # summarize all
    for tid, entries in time_data.items():
        total = sum(duration_seconds(e.get("start"), e.get("stop")) for e in entries)
        print(f"{tid}: {format_seconds(total)} across {len(entries)} entries")
    print()
