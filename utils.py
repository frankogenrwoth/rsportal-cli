import json
from pathlib import Path
import os
import keyring

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    # dotenv is optional; if missing, fall back to OS env only
    pass

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


def get_api_base() -> str:
    """Resolve the API base URL including `/api/v1`.

    Resolution order:
    - RSPORTAL_BASE_URL (preferred)
    - RSPORTAL_API_BASE (backward-compat)
    - default: http://localhost:8000

    Appends `/api/v1` and strips trailing slashes.
    """
    base = (
        os.environ.get("RSPORTAL_BASE_URL")
        or os.environ.get("RSPORTAL_API_BASE")
        or "http://localhost:8000"
    )
    base = base.rstrip("/")
    return f"{base}/api/v1"


def get_basic_auth():
    """Return (username, password) tuple for HTTP Basic auth, or (None, None)."""
    if not AUTH_FILE.exists():
        return None, None
    try:
        data = json.loads(AUTH_FILE.read_text())
    except Exception:
        return None, None
    active_user = data.get("active_user") or {}
    username = active_user.get("username")
    if not username:
        return None, None
    password = keyring.get_password("rsportal", username)
    if not password:
        return None, None
    return username, password


def get_authed_session():
    """Create a requests.Session authenticated via Django/DRF SessionAuth.

    Logs in via Django's login view at BASE_URL/accounts/login/ using CSRF,
    then returns a session with cookies set. Returns None on failure.
    """
    try:
        import requests
    except Exception:
        return None

    username, password = get_basic_auth()
    if not (username and password):
        return None

    api_base = get_api_base()
    site_base = api_base.rsplit("/api/v1", 1)[0]
    login_url = f"{site_base}/accounts/login/"
    s = requests.Session()
    try:
        # 1) GET login page to obtain CSRF cookie
        r1 = s.get(login_url, timeout=15)
        csrftoken = s.cookies.get("csrftoken") or s.cookies.get("csrf")
        headers = {"Referer": login_url}
        data = {"username": username, "password": password}
        if csrftoken:
            headers["X-CSRFToken"] = csrftoken
            data["csrfmiddlewaretoken"] = csrftoken
        # 2) POST credentials (form-encoded) to login
        # Debug: print payload sample (password masked) when RSPORTAL_DEBUG is truthy
        try:
            if os.environ.get("RSPORTAL_DEBUG"):
                print("\n[DEBUG] Login request payload:")
                print(f"URL: {login_url}")
                print("Method: POST")
                print("Headers:")
                for k, v in headers.items():
                    safe_v = "***" if k.lower().startswith("x-csrf") else v
                    print(f"  {k}: {safe_v}")
                print("Data:")
                print(f"  username: {data.get('username')}")
                print("  password: ***")
                masked_csrf = "***" if data.get("csrfmiddlewaretoken") else None
                print(f"  csrfmiddlewaretoken: {masked_csrf}")
                print()
        except Exception:
            pass
        r2 = s.post(
            login_url, data=data, headers=headers, timeout=15, allow_redirects=True
        )
        # 3) Probe auth check to confirm session (avoid 302 to login)
        probe = s.get(
            f"{api_base}/auth/check",
            timeout=10,
            headers={"Referer": site_base},
            allow_redirects=False,
        )
        if probe.status_code in (200, 204):
            return s
    except Exception:
        pass
    return None
