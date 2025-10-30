## Time Tracking

Time tracking is performed from the GUI. Typical workflow:

- Select a task in the Tasks view and click "Start" to begin a time entry for that task.
- Click "Stop" on the running entry (from the task row or the Time view) to end it.
- The Time/Logs view shows an overview of running and completed entries, and per-task history.

Behavior:
- Starting a task stops any other running task automatically.
- Entries are stored in the application database at `~/.rsportal/rsportal.db` (SQLite).
- When stopping an entry the UI will prompt for notes if none were provided.
