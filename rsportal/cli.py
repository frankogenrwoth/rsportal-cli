import argparse
from rsportal.commands import auth_cmd, time_cmd, push_cmd, log_cmd, tasks_cmd, pull_cmd


def main():
    parser = argparse.ArgumentParser(prog="rsportal", description="RSportal CLI tool.")
    subparsers = parser.add_subparsers(dest="command")

    # rsportal auth
    auth_parser = subparsers.add_parser(
        "auth",
        help="Authenticate RSportal with your account details password and username.",
    )
    auth_subparsers = auth_parser.add_subparsers(dest="auth_cmd")
    auth_subparsers.add_parser("login", help="Login to RSportal.")
    auth_subparsers.add_parser("logout", help="Logout from RSportal.")
    auth_subparsers.add_parser("status", help="Show current auth status.")
    auth_subparsers.add_parser("verify", help="Verify credentials with the server.")

    auth_parser.add_argument("--login", action="store_true", help="Login to RSportal.")
    auth_parser.add_argument(
        "--logout", action="store_true", help="Logout from RSportal."
    )
    auth_parser.add_argument(
        "--status", action="store_true", help="Check if you are logged in to RSportal."
    )
    auth_parser.set_defaults(func=auth_cmd.handle)

    # rsportal time
    time_parser = subparsers.add_parser(
        "time", help="Time tracking for tasks and projects."
    )
    time_subparsers = time_parser.add_subparsers(dest="time_cmd")
    time_subparsers.add_parser("start", help="Start time tracking for a task.")
    time_subparsers.add_parser(
        "stop", help="Stop time tracking for a task or all tasks."
    )
    time_subparsers.add_parser("status", help="Show time tracking status.")

    time_parser.add_argument(
        "--start", action="store_true", help="Start time tracking for a task."
    )
    time_parser.add_argument(
        "--stop",
        action="store_true",
        help="Stop time tracking for a task or all tasks.",
    )
    time_parser.add_argument(
        "--status", action="store_true", help="Show time tracking status."
    )
    time_parser.add_argument(
        "-t", "--task-id", dest="task_id", help="Task ID for time tracking operations."
    )
    time_parser.add_argument(
        "-n",
        "--notes",
        dest="notes",
        help="Notes for the time entry (if omitted on stop, editor opens)",
        default=None,
    )
    time_parser.set_defaults(func=time_cmd.handle)

    # rsportal push
    push_parser = subparsers.add_parser(
        "push",
        help="Sync local time entries to remote server and manage sync operations.",
    )
    push_subparsers = push_parser.add_subparsers(dest="push_cmd")
    push_subparsers.add_parser("sync", help="Sync local time entries to remote server.")
    push_subparsers.add_parser("status", help="Show sync status and history.")

    push_parser.add_argument(
        "--sync", action="store_true", help="Sync local time entries to remote server."
    )
    push_parser.add_argument(
        "--status", action="store_true", help="Show sync status and history."
    )
    push_parser.set_defaults(func=push_cmd.handle)

    # rsportal log
    log_parser = subparsers.add_parser("log", help="View time logs and summaries.")
    log_subparsers = log_parser.add_subparsers(dest="log_cmd")
    log_subparsers.add_parser("show", help="Show detailed time log entries.")
    log_subparsers.add_parser("summary", help="Show total time per task.")

    log_parser.add_argument("--show", action="store_true", help="Show log entries.")
    log_parser.add_argument(
        "--summary", action="store_true", help="Show time summary per task."
    )
    log_parser.add_argument(
        "-t", "--task-id", dest="task_id", help="Filter by task ID."
    )
    log_parser.set_defaults(func=log_cmd.handle)

    # rsportal tasks
    tasks_parser = subparsers.add_parser(
        "tasks", help="View and annotate tasks (pulled from server)."
    )
    tasks_subparsers = tasks_parser.add_subparsers(dest="tasks_cmd")
    tasks_subparsers.add_parser("list", help="List tasks.")
    tasks_subparsers.add_parser("edit", help="Edit a task's objective and local notes.")
    review_parser = tasks_subparsers.add_parser(
        "review", help="Request PM/CTO review for a task."
    )
    review_parser.add_argument(
        "-i", "--task-id", dest="task_id", required=True, help="Task ID"
    )
    review_parser.add_argument(
        "--pm", action="store_true", help="Set status to PM_REVIEW"
    )
    review_parser.add_argument(
        "--cto", action="store_true", help="Set status to CTO_REVIEW"
    )

    tasks_parser.add_argument("--list", action="store_true", help="List tasks.")
    tasks_parser.add_argument(
        "--urgency",
        choices=["LOW", "MEDIUM", "HIGH", "CRITICAL"],
        help="Filter by urgency",
    )
    tasks_parser.add_argument(
        "--due-before", dest="due_before", help="Filter tasks due on/before YYYY-MM-DD"
    )
    tasks_parser.add_argument(
        "--due-after", dest="due_after", help="Filter tasks due on/after YYYY-MM-DD"
    )
    tasks_parser.add_argument(
        "-t",
        "--title",
        dest="title",
        help="(Deprecated) not used for remote tasks.",
    )
    tasks_parser.add_argument(
        "-i", "--task-id", dest="task_id", help="Task ID for operations."
    )
    tasks_parser.set_defaults(func=tasks_cmd.handle)

    # rsportal pull
    pull_parser = subparsers.add_parser(
        "pull", help="Pull data from remote (e.g., tasks)."
    )
    pull_subparsers = pull_parser.add_subparsers(dest="pull_cmd")
    pull_subparsers.add_parser("tasks", help="Pull assigned tasks from server.")

    pull_parser.add_argument(
        "--tasks", action="store_true", help="Pull assigned tasks from server."
    )
    pull_parser.set_defaults(func=pull_cmd.handle)

    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()
