## Time Tracking

Start/Stop per task:
```
python main.py time start -t TASK-123
python main.py time stop -t TASK-123   # stop one
python main.py time stop               # stop all running
python main.py time status             # overview
python main.py time status -t TASK-123 # per-task
```

Behavior:
- Starting a task stops other running tasks
- Entries stored in `~/.rsportal/time.json` as `start_time`/`end_time` pairs
 - On stop, if you don't pass `-n/--notes`, an editor opens to capture notes
