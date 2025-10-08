# rsportal/commands/push_cmd.py
import keyring
from pathlib import Path
from datetime import datetime
from utils import require_auth
from rsportal.storage import (
    load_time,
    save_time,
    load_sync_log,
    save_sync_log,
    load_tasks,
)

try:
    import requests

    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

SERVICE_NAME = "rsportal"
TIME_FILE = Path.home() / ".rsportal" / "time.json"
AUTH_FILE = Path.home() / ".rsportal" / "auth.json"

# Ensure directories exist
TIME_FILE.parent.mkdir(parents=True, exist_ok=True)


def handle(args):
    # Require authentication for push operations
    require_auth()

    # Handle subcommands
    if getattr(args, "push_cmd", None) == "sync":
        do_sync()
        return
    elif getattr(args, "push_cmd", None) == "status":
        do_sync_status()
        return

    # Handle flags for backward compatibility
    if getattr(args, "sync", False):
        do_sync()
        return
    elif getattr(args, "status", False):
        do_sync_status()
        return

    # Default behavior: sync
    do_sync()


def load_time_data():
    return load_time()


def save_time_data(data):
    save_time(data)


def load_sync_log_local():
    return load_sync_log()


def save_sync_log_local(sync_log):
    save_sync_log(sync_log)


def get_auth_credentials():
    """Get authentication credentials"""
    if not AUTH_FILE.exists():
        return None, None

    try:
        with open(AUTH_FILE, "r") as f:
            data = json.load(f)
            active_user = data.get("active_user")
            if active_user and active_user.get("username"):
                username = active_user["username"]
                password = keyring.get_password(SERVICE_NAME, username)
                return username, password
    except:
        pass

    return None, None


def get_completed_entries(time_data):
    """Get all completed time entries (those with both start and end times)."""
    completed_entries = []

    for task_id, entries in time_data.items():
        for entry in entries:
            start_val = entry.get("start_time") or entry.get("start")
            stop_val = entry.get("end_time") or entry.get("stop")
            if start_val and stop_val:
                completed_entries.append(
                    {
                        "task_id": task_id,
                        "start_time": start_val,
                        "end_time": stop_val,
                        "notes": entry.get("notes", ""),
                        "duration": calculate_duration(start_val, stop_val),
                    }
                )

    return completed_entries


def calculate_duration(start_str, stop_str):
    """Calculate duration in seconds between start and stop times"""
    try:
        start = datetime.fromisoformat(start_str)
        stop = datetime.fromisoformat(stop_str)
        return int((stop - start).total_seconds())
    except:
        return 0


def sync_to_remote(entries, username, password):
    """Simulate syncing entries to remote server"""
    # This is a mock implementation - replace with actual API endpoint
    # For now, we'll simulate the sync process

    synced_entries = []
    failed_entries = []

    print(f"Syncing {len(entries)} time entries to remote server...")

    for entry in entries:
        try:
            # Simulate API call delay and processing
            print(
                f"  Syncing task {entry['task_id']}: {entry['start_time']} - {entry['end_time']}"
            )

            # Mock API call - replace with actual implementation
            # response = requests.post(
            #     "https://api.rsportal.com/time/entries",
            #     json=entry,
            #     auth=(username, password),
            #     timeout=30
            # )
            #
            # if response.status_code == 200:
            #     synced_entries.append(entry)
            # else:
            #     failed_entries.append({
            #         "entry": entry,
            #         "error": f"HTTP {response.status_code}: {response.text}"
            #     })

            # For mock purposes, assume all entries sync successfully
            synced_entries.append(entry)

        except Exception as e:
            failed_entries.append({"entry": entry, "error": str(e)})

    return synced_entries, failed_entries


def remove_synced_entries(time_data, synced_entries):
    """Remove successfully synced entries from local time data"""
    entries_to_remove = {}

    # Group synced entries by task_id
    for entry in synced_entries:
        task_id = entry["task_id"]
        if task_id not in entries_to_remove:
            entries_to_remove[task_id] = []
        entries_to_remove[task_id].append(
            {"start": entry["start"], "stop": entry["stop"]}
        )

    # Remove synced entries from time data
    for task_id, entries_list in entries_to_remove.items():
        if task_id in time_data:
            original_entries = time_data[task_id]
            filtered_entries = []

            for original_entry in original_entries:
                # Keep entry if it's not in the synced list or if it's still running
                should_keep = True

                if original_entry.get("stop"):  # Only remove completed entries
                    for synced_entry in entries_list:
                        if (
                            original_entry.get("start") == synced_entry["start"]
                            and original_entry.get("stop") == synced_entry["stop"]
                        ):
                            should_keep = False
                            break

                if should_keep:
                    filtered_entries.append(original_entry)

            if filtered_entries:
                time_data[task_id] = filtered_entries
            else:
                del time_data[task_id]

    return time_data


def do_sync():
    """Sync local time changes to remote and clear synced records"""
    print("\nStarting sync process...")

    # Load current time data
    time_data = load_time_data()
    tasks_data = load_tasks()

    if not time_data:
        print("No time tracking data found to sync.\n")
        return

    # Get authentication credentials
    username, password = get_auth_credentials()
    if not username or not password:
        print("Error: Authentication credentials not found. Please login first.\n")
        return

    # Get completed entries that need to be synced
    completed_entries = get_completed_entries(time_data)

    # Enforce: Task must have both title and objective to be pushed
    valid_task_ids = set()
    for t in tasks_data or []:
        tid = t.get("id")
        title = (t.get("title") or "").strip()
        objective = (t.get("objective") or "").strip()
        if tid and title and objective:
            valid_task_ids.add(tid)

    pre_filter_count = len(completed_entries)
    completed_entries = [
        e for e in completed_entries if e.get("task_id") in valid_task_ids
    ]
    skipped_count = pre_filter_count - len(completed_entries)

    if not completed_entries:
        if skipped_count > 0:
            print(
                "No eligible entries to sync. Ensure tasks have both title and description."
            )
        else:
            print("No completed time entries found to sync.")
        print()
        return

    print(f"Found {len(completed_entries)} completed entries to sync.")
    if skipped_count > 0:
        print(f"Skipped {skipped_count} entries (missing task title/description).")

    # Check for any currently running tasks
    running_tasks = []
    for task_id, entries in time_data.items():
        if entries and entries[-1].get("stop") is None:
            running_tasks.append(task_id)

    if running_tasks:
        print(
            f"Warning: The following tasks are still running: {', '.join(running_tasks)}"
        )
        print("Only completed entries will be synced.")

    # Sync to remote
    synced_entries, failed_entries = sync_to_remote(
        completed_entries, username, password
    )

    # Update sync log
    sync_log = load_sync_log_local()
    sync_log["last_sync"] = datetime.now().isoformat()
    sync_log["synced_entries"].extend(synced_entries)
    sync_log["failed_entries"].extend(failed_entries)
    save_sync_log_local(sync_log)

    # Report results
    print(f"\nSync completed:")
    print(f"  Successfully synced: {len(synced_entries)} entries")
    if failed_entries:
        print(f"  Failed to sync: {len(failed_entries)} entries")
        print("  Check sync status for details on failed entries.")

    # Remove successfully synced entries from local data
    if synced_entries:
        updated_time_data = remove_synced_entries(time_data, synced_entries)
        save_time_data(updated_time_data)
        print(f"  Cleared {len(synced_entries)} synced entries from local storage")

    print()


def do_sync_status():
    """Show sync status and history"""
    sync_log = load_sync_log()
    time_data = load_time_data()

    print("\nSync Status")
    print("===========")

    if sync_log["last_sync"]:
        print(f"Last sync: {sync_log['last_sync']}")
    else:
        print("Never synced")

    print(f"Total synced entries: {len(sync_log['synced_entries'])}")
    print(f"Failed sync attempts: {len(sync_log['failed_entries'])}")

    # Show pending entries
    completed_entries = get_completed_entries(time_data)
    print(f"Pending sync entries: {len(completed_entries)}")

    # Show running tasks
    running_tasks = []
    for task_id, entries in time_data.items():
        if entries and entries[-1].get("stop") is None:
            running_tasks.append(task_id)

    if running_tasks:
        print(f"Currently running tasks: {', '.join(running_tasks)}")

    # Show failed entries details if any
    if sync_log["failed_entries"]:
        print("\nFailed Entries:")
        print("---------------")
        for i, failed in enumerate(
            sync_log["failed_entries"][-5:], 1
        ):  # Show last 5 failures
            entry = failed["entry"]
            print(f"{i}. Task: {entry['task_id']}")
            print(f"   Time: {entry['start']} - {entry['stop']}")
            print(f"   Error: {failed['error']}")

    # Show recent synced entries
    if sync_log["synced_entries"]:
        print("\nRecent Synced Entries:")
        print("----------------------")
        for i, entry in enumerate(
            sync_log["synced_entries"][-5:], 1
        ):  # Show last 5 synced
            print(f"{i}. Task: {entry['task_id']}")
            print(f"   Time: {entry['start']} - {entry['stop']}")
            print(f"   Duration: {entry['duration']}s")

    print()


def show_help():
    help_text = """
RSportal Push Commands

Usage:
  rsportal push [subcommand]
  rsportal push [flags]

Subcommands:
  sync          Sync local time entries to remote server and clear synced records
  status        Show sync status and history

Flags (backward compatibility):
  --sync        Sync local time entries to remote server and clear synced records
  --status      Show sync status and history

Examples:
  rsportal push sync        # Sync completed time entries to remote
  rsportal push status      # Show sync status and pending entries
  rsportal push             # Default behavior: sync

Behavior:
  - Only completed time entries (with both start and stop times) are synced
  - Successfully synced entries are removed from local storage
  - Failed sync attempts are logged for retry
  - Running tasks are not affected by sync operations
  - Authentication is required for push operations
  - Sync log is stored in ~/.rsportal/sync_log.json
"""
    print(help_text)
