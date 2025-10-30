## Quickstart

- Install dependencies (optional): `pip install -r requirements.txt`
- Launch the application GUI:

```
python main.py
```

On Windows you can run the same from PowerShell or cmd. If you prefer setting environment
variables first, here are examples (PowerShell / cmd):

PowerShell:

```
$env:RSPORTAL_API_BASE = "https://your.api"
```

cmd.exe:

```
set RSPORTAL_API_BASE=https://your.api
```

- Sign in using the application's Authentication dialog (open the "Sign in" or "Auth" menu).
- Pull tasks from the server using the "Pull" action in the UI (Tasks view).
- Start/stop time tracking directly from the Tasks/time UI (select task, click Start/Stop).
- View logs and summaries from the Logs view in the GUI.

Notes:
- The application is GUI-first — previous CLI commands are deprecated. Most operations
	(auth, pull, push/sync, time tracking) are available from the interface.
