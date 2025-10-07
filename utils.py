import json
from pathlib import Path

AUTH_FILE = Path.home() / ".rsportal" / "auth.json"


def require_auth():
    if not AUTH_FILE.exists():
        print("\nAuthentication required. Run 'rsportal auth --login'\n")
        exit(1)

    data = json.loads(AUTH_FILE.read_text())
    return data.get("active_user")
