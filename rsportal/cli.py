import argparse
from rsportal.commands import auth_cmd, time_cmd


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
    time_parser.set_defaults(func=time_cmd.handle)

    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()
