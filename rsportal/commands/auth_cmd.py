# rsportal/commands/auth_cmd.py
import keyring
import getpass
import json
from pathlib import Path

SERVICE_NAME = "rsportal"
CRED_FILE = Path.home() / ".rsportal" / "auth.json"
CRED_FILE.parent.mkdir(parents=True, exist_ok=True)


def handle(args):
    # Route subcommands if provided (rsportal auth login/logout/status)
    if getattr(args, "auth_cmd", None) == "login":
        login()
        return
    if getattr(args, "auth_cmd", None) == "logout":
        logout()
        return
    if getattr(args, "auth_cmd", None) == "status":
        check_auth()
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

    # Example validation (in a real app, you'd call your API here)
    if username and password:
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
