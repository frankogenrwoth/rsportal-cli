# rsportal/commands/auth_cmd.py
import keyring
import getpass
import json
from pathlib import Path
import os
from utils import get_api_base

SERVICE_NAME = "rsportal"
CRED_FILE = Path.home() / ".rsportal" / "auth.json"
CRED_FILE.parent.mkdir(parents=True, exist_ok=True)


def handle(args):
    if getattr(args, "help", False):
        show_help()
        return

    if getattr(args, "auth_cmd", None) == "login":
        login()
        return
    if getattr(args, "auth_cmd", None) == "logout":
        logout()
        return
    if getattr(args, "auth_cmd", None) == "status":
        check_auth()
        return
    if getattr(args, "auth_cmd", None) == "verify":
        verify()
        return

    # Backward compatibility: flags still work
    if getattr(args, "login", False):
        login()
        return
    if getattr(args, "logout", False):
        logout()
        return
    if getattr(args, "status", False):
        check_auth()
        return

    # Default behavior: if logged out, prompt login; else show status
    if not is_logged_in():
        login()
    else:
        check_auth()


def login():
    username = input("Username: ")
    password = getpass.getpass("Password: ")

    # Verify with backend if possible
    if username and password and verify_credentials(username, password):
        keyring.set_password(SERVICE_NAME, username, password)

        # Save the active user info
        CRED_FILE.write_text(
            json.dumps(
                {"active_user": {"username": username, "password": password}}, indent=2
            )
        )
        print(f"\nLogged in as {username}\n")
    else:
        print("\nInvalid credentials\n")


def logout():
    if CRED_FILE.exists():
        data = json.loads(CRED_FILE.read_text())
        active_user = data.get("active_user")
        if active_user:
            username = active_user.get("username")
            if username:
                keyring.delete_password(SERVICE_NAME, username)
            data["active_user"] = None
            CRED_FILE.write_text(json.dumps(data, indent=2))
            print("\nLogged out successfully.\n")
        else:
            print("\nNo active session.\n")
    else:
        print("\nNo active session.\n")


def check_auth():
    if not CRED_FILE.exists():
        print("\nNo user logged in. Use 'rsportal auth --login' first.\n")
        return
    try:
        data = json.loads(CRED_FILE.read_text())
    except Exception:
        print("\nAuth data is corrupted. Please login again: 'rsportal auth --login'\n")
        return
    active_user = data.get("active_user")
    username = active_user.get("username") if isinstance(active_user, dict) else None
    if not username:
        print("\nNo user logged in. Use 'rsportal auth --login' first.\n")
        return
    print(f"\nLogged in as: {username}\n")


def verify():
    if not CRED_FILE.exists():
        print("\nNo credentials saved. Use 'rsportal auth login' first.\n")
        return
    try:
        data = json.loads(CRED_FILE.read_text())
    except Exception:
        print("\nAuth data is corrupted.\n")
        return
    active_user = data.get("active_user") or {}
    username = active_user.get("username")
    if not username:
        print("\nNo user logged in.\n")
        return
    password = keyring.get_password(SERVICE_NAME, username)
    if not password:
        print("\nPassword not found in keyring. Re-login.\n")
        return
    ok = verify_credentials(username, password)
    print("\nCredentials valid.\n" if ok else "\nInvalid credentials.\n")


def verify_credentials(username: str, password: str) -> bool:
    try:
        import requests

        base = get_api_base()
        url = f"{base}/auth/check"
        resp = requests.get(url, auth=(username, password), timeout=15)
        return resp.status_code in (200, 204)
    except Exception:
        # If server unreachable, fallback to basic local check
        return bool(username and password)


def is_logged_in():
    if not CRED_FILE.exists():
        return False
    try:
        data = json.loads(CRED_FILE.read_text())
    except Exception:
        return False
    active_user = data.get("active_user")
    username = active_user.get("username") if isinstance(active_user, dict) else None
    return bool(username)


def show_help():
    help_text = """
        RSportal Auth Commands:

        Usage:
        rsportal auth [subcommand]
        rsportal auth [flags]

        Subcommands:
        login         Login to RSportal with your credentials
        logout        Logout from RSportal and clear stored credentials  
        status        Check current authentication status

        Flags (backward compatibility):
        --login       Login to RSportal with your credentials
        --logout      Logout from RSportal and clear stored credentials
        --status      Check current authentication status
        -h, --help    Show this help message

        Examples:
        rsportal auth login         # Login using subcommand
        rsportal auth --login       # Login using flag (backward compatibility)
        rsportal auth status        # Check auth status
        rsportal auth -h            # Show this help
        rsportal auth --help        # Show this help

        Default behavior:
        If no subcommand or flag is provided, the command will prompt for login
        if not authenticated, or show current status if already logged in.
    """
    print(help_text)
