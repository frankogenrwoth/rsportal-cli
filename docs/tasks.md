## Tasks

Tasks are pulled from the server and stored locally for offline reference. Creation/removal/status changes are server-managed.

- Pull tasks: `python main.py pull tasks`
- List tasks: `python main.py tasks list`
- Filter by urgency/deadline:
  - `python main.py tasks list --urgency HIGH`
  - `python main.py tasks list --due-before 2025-12-31`
  - `python main.py tasks list --due-after 2025-10-01`
- View/edit details: `python main.py tasks edit -i TASK-123`
Request review:
```
python main.py tasks review -i TASK-123 --pm    # set status to PM_REVIEW
python main.py tasks review -i TASK-123 --cto   # set status to CTO_REVIEW
```
  - Editor format:
    - First line: Title (read-only)
    - Section "Objective:": editable; aligns with backend required field
    - Section "Local Notes:": your private notes, kept locally

Push precondition: time entries only sync for tasks that have both a non-empty Title and Objective.

Local storage: `~/.rsportal/tasks.json`
