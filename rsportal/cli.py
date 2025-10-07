import argparse
from rsportal.commands import auth_cmd


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

    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()
