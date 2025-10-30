## Authentication

Authentication is handled from the GUI via the Authentication dialog.

How to sign in:
- Open the application and choose "Sign in" from the Auth menu or the welcome dialog.
- Enter your username and password in the dialog; you can choose to save credentials locally.

Status and logout:
- Use the Auth menu in the application to view current auth status or to sign out.

Storage:
- The app stores non-sensitive session/state in the application storage (SQLite DB at `~/.rsportal/rsportal.db`).
- Passwords (if saved) are stored in the system keyring via the `keyring` library when available.
