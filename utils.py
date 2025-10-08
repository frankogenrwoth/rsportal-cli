import json
from pathlib import Path

AUTH_FILE = Path.home() / ".rsportal" / "auth.json"


def require_auth():
    if not AUTH_FILE.exists():
        print("\nAuthentication required. Run 'rsportal auth --login'\n")
        exit(1)

    data = json.loads(AUTH_FILE.read_text())
    return data.get("active_user")


def is_authenticated() -> bool:
    if not AUTH_FILE.exists():
        return False

    try:
        data = json.loads(AUTH_FILE.read_text())
    except Exception:
        return False

    active_user = data.get("active_user")
    username = active_user.get("username") if isinstance(active_user, dict) else None
    return True if bool(username) else False
