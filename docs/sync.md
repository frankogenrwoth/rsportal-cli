## Pull & Push

The application provides Pull and Push (Sync) actions in the GUI:

- Pull tasks: use the "Pull" action in the Tasks view to fetch assigned tasks from the server.
    - Requires `RSPORTAL_API_BASE` (set via environment or application configuration).
    - Server data is merged with local notes managed in the app.

- Push (sync) time entries: use the Sync or Push button in the Time/Sync view.
    - The GUI syncs completed entries only and will present the result in the UI.
    - Sync history and metadata are recorded in the application storage (SQLite DB at `~/.rsportal/rsportal.db`).
    - The UI will show skipped entries and reasons when entries are not eligible for push.
