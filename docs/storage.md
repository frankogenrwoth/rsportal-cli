## Storage Layout

The application now uses a SQLite-backed storage by default.

- Primary DB: `~/.rsportal/rsportal.db` — contains tasks, time entries, comments, docs, and auth table used by the GUI.

Legacy JSON files (deprecated):
- `~/.rsportal/auth.json`, `~/.rsportal/tasks.json`, `~/.rsportal/time.json`, and `~/.rsportal/sync_log.json`

If you are migrating from an older installation that used JSON files, the GUI/migration tools
will attempt to migrate data to SQLite where applicable. Back up your `~/.rsportal/` directory
before running migrations.
