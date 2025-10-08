## Pull & Push

Pull tasks from server:
```
python main.py pull tasks
```
- Requires `RSPORTAL_API_BASE`
- Merges server data with local notes (preserves `description`)

Push time entries (mock sync):
```
python main.py push sync
python main.py push status
```
- Synces completed entries only
- Stores sync history in `~/.rsportal/sync_log.json`
 - Only entries for tasks with both a non-empty title and description are pushed
  - (Title + Objective) are required; Description refers to Objective in backend terms
  - If entries are skipped, the CLI prints how many were skipped and why
