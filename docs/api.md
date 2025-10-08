## API

- Base URL: `RSPORTAL_API_BASE`

### Tasks
- GET `/tasks/assigned` → array of Task
- Task fields (subset shown):
  - `id`, `project`, `title`, `task_id_link`, `assigner`, `assignee`
  - `category` ∈ {MAINTENANCE, RESEARCH, AUTOMATION, WEBSITE, CODING, MARKETING, DESIGN, SALES, TESTING, GENERAL}
  - `status` ∈ {TODO, IN_PROGRESS, BLOCKED, PM_REVIEW, CTO_REVIEW, COMPLETED}
  - `urgency` ∈ {LOW, MEDIUM, HIGH, CRITICAL}
  - `deadline` (YYYY-MM-DD)
  - `objective`, `summary`, `documentation` (object), `credentials`
  - approvals: `pm_approved`, `pm_reviewer`, `cto_approved`, `cto_reviewer`
  - `created_at`, `updated_at`

### Time Entries (push)
- POST `/time/entries` → create entry
- Payload per entry:
```
{
  "task_id": "TASK-123",
  "start_time": "2025-10-08T12:34:56",
  "end_time": "2025-10-08T13:10:02",
  "notes": "optional"
}
```
- Server computes duration; client may include it if accepted.

### Auth
- Uses credentials from CLI login; provide Authorization header as required (Basic/Bearer).
