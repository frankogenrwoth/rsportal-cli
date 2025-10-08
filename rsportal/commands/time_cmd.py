# rsportal/commands/time_cmd.py
import json
from pathlib import Path
from datetime import datetime
import sys
from utils import require_auth

TIME_FILE = Path.home() / ".rsportal" / "time.json"
TIME_FILE.parent.mkdir(parents=True, exist_ok=True)


def handle(args):
    # Require authentication for time tracking
    require_auth()

    task_id = getattr(args, "task_id", None)

    # Handle subcommands
    if getattr(args, "time_cmd", None) == "start":
        do_start(task_id)
        return
    elif getattr(args, "time_cmd", None) == "stop":
        do_stop(task_id)
        return
    elif getattr(args, "time_cmd", None) == "status":
        do_status(task_id)
        return

    # Handle flags for backward compatibility
    if getattr(args, "start", False):
        do_start(task_id)
        return
    elif getattr(args, "stop", False):
        do_stop(task_id)
        return
    elif getattr(args, "status", False):
        do_status(task_id)
        return

    # Default behavior: show status
    do_status(task_id)


def load_time_data():
    """Load time tracking data from file"""
    if not TIME_FILE.exists():
        return {}
    try:
        with open(TIME_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def save_time_data(data):
    """Save time tracking data to file"""
    with open(TIME_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_running_tasks(data):
    """Get list of currently running tasks"""
    running = []
    for task_id, entries in data.items():
        if entries and entries[-1].get("stop") is None:
            running.append(task_id)
    return running


def do_start(task_id):
    if not task_id:
        print("\nError: Task ID is required to start time tracking.")
        print("Use: rsportal time start -t <task_id>\n")
        return

    data = load_time_data()

    # Stop all other running tasks
    running_tasks = get_running_tasks(data)
    stopped_tasks = []

    for running_id in running_tasks:
        if running_id != task_id:
            # Stop the running task
            current_time = datetime.now().isoformat()
            data[running_id][-1]["stop"] = current_time
            stopped_tasks.append(running_id)

    # Initialize task if it doesn't exist
    if task_id not in data:
        data[task_id] = []

    # Check if this task is already running
    if task_id in running_tasks:
        print(f"\nTask '{task_id}' is already running.\n")
        return

    # Start new entry for this task
    start_time = datetime.now().isoformat()
    data[task_id].append({"start": start_time, "stop": None})

    save_time_data(data)

    if stopped_tasks:
        print(f"\nStopped tasks: {', '.join(stopped_tasks)}")
    print(f"Started tracking task: {task_id}")
    print(f"Started at: {start_time}\n")


def do_stop(task_id=None):
    data = load_time_data()

    if not data:
        print("\nNo time tracking data found.\n")
        return

    running_tasks = get_running_tasks(data)

    if not running_tasks:
        print("\nNo tasks are currently running.\n")
        return

    if task_id:
        # Stop specific task
        if task_id not in running_tasks:
            print(f"\nTask '{task_id}' is not currently running.\n")
            return

        current_time = datetime.now().isoformat()
        data[task_id][-1]["stop"] = current_time
        save_time_data(data)
        print(f"\nStopped task: {task_id}")
        print(f"Stopped at: {current_time}\n")
    else:
        # Stop all running tasks
        current_time = datetime.now().isoformat()
        for running_id in running_tasks:
            data[running_id][-1]["stop"] = current_time

        save_time_data(data)
        print(f"\nStopped all running tasks: {', '.join(running_tasks)}")
        print(f"Stopped at: {current_time}\n")


def format_duration(start_str, stop_str=None):
    """Calculate and format duration between start and stop times"""
    try:
        start = datetime.fromisoformat(start_str)
        if stop_str:
            stop = datetime.fromisoformat(stop_str)
        else:
            stop = datetime.now()

        duration = stop - start
        total_seconds = int(duration.total_seconds())

        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    except:
        return "Invalid duration"


def do_status(task_id=None):
    data = load_time_data()

    if not data:
        print("\nNo time tracking data found.\n")
        return

    if task_id:
        # Show status for specific task
        if task_id not in data:
            print(f"\nTask '{task_id}' not found.\n")
            return

        entries = data[task_id]
        if not entries:
            print(f"\nTask '{task_id}' has no time entries.\n")
            return

        print(f"\nTask: {task_id}")
        print("=" * (len(task_id) + 6))

        total_duration = 0
        for i, entry in enumerate(entries, 1):
            start = entry["start"]
            stop = entry.get("stop")
            duration = format_duration(start, stop)
            status = "RUNNING" if stop is None else "STOPPED"

            print(f"Entry {i}: {start} - {stop or 'RUNNING'} ({duration}) [{status}]")

            # Calculate total duration for completed entries
            if stop:
                try:
                    start_dt = datetime.fromisoformat(start)
                    stop_dt = datetime.fromisoformat(stop)
                    total_duration += (stop_dt - start_dt).total_seconds()
                except:
                    pass

        # Add current running time if applicable
        running_entry = next((e for e in entries if e.get("stop") is None), None)
        if running_entry:
            try:
                start_dt = datetime.fromisoformat(running_entry["start"])
                current_duration = (datetime.now() - start_dt).total_seconds()
                total_duration += current_duration
            except:
                pass

        # Format total duration
        hours = int(total_duration // 3600)
        minutes = int((total_duration % 3600) // 60)
        seconds = int(total_duration % 60)

        total_str = (
            f"{hours}h {minutes}m {seconds}s"
            if hours > 0
            else f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"
        )
        print(f"Total time: {total_str}\n")

    else:
        # Show status for all tasks
        running_tasks = get_running_tasks(data)

        print("\nTime Tracking Status")
        print("===================")

        if running_tasks:
            print(f"Currently running: {', '.join(running_tasks)}")
        else:
            print("No tasks currently running")

        print(f"\nAll tracked tasks:")
        for task_id, entries in data.items():
            if entries:
                latest = entries[-1]
                status = "RUNNING" if latest.get("stop") is None else "STOPPED"
                entry_count = len(entries)
                print(f"  {task_id}: {entry_count} entries, {status}")

        print()


def do_help():
    pass


def show_help():
    help_text = """
RSportal Time Tracking Commands

Usage:
  rsportal time [subcommand] -t <task_id>
  rsportal time [flags] -t <task_id>

Subcommands:
  start         Start time tracking for a task (requires -t <task_id>)
  stop          Stop time tracking for a task or all tasks
  status        Show time tracking status

Flags (backward compatibility):
  --start       Start time tracking for a task (requires -t <task_id>)
  --stop        Stop time tracking for a task or all tasks
  --status      Show time tracking status
  -t <task_id>  Specify task ID for time tracking operations

Examples:
  rsportal time start -t TASK-123      # Start tracking task TASK-123
  rsportal time stop -t TASK-123       # Stop tracking task TASK-123
  rsportal time stop                   # Stop all running tasks
  rsportal time status -t TASK-123     # Show status for task TASK-123
  rsportal time status                 # Show status for all tasks

Behavior:
  - Starting a task automatically stops all other running tasks
  - Time entries are stored in ~/.rsportal/time.json
  - Format: {"<task_id>": [{"start": "timestamp", "stop": "timestamp"}, ...]}
  - Authentication is required for time tracking operations
"""
    print(help_text)
