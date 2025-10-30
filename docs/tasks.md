## Tasks

Tasks are pulled from the server and available in the Tasks view for offline reference. Creation,
removal, and authoritative status changes are server-managed.

- Pull tasks: open the Tasks view and click the "Pull" or "Refresh" button to fetch assigned tasks.
- List and filtering: use the Tasks view filters to restrict by urgency, due date, or other fields.
  - Example filters available in the UI: Urgency, Due Before, Due After.
- View/edit details: select a task and click "Edit" to change Objective or add Local Notes.

Request review:
- Use the Review action/button on a task to request PM or CTO review. The dialog provides options
  to set PM_REVIEW or CTO_REVIEW status.

Editor format:
- Title: displayed read-only in the task editor.
- Objective: editable (this maps to the backend required field).
- Local Notes: private notes kept locally in the application.

Push precondition: time entries only sync for tasks that have both a non-empty Title and Objective.

Local storage: tasks are stored in the application database at `~/.rsportal/rsportal.db` (SQLite).
