## Configuration

- Environment variables:
  - `RSPORTAL_API_BASE`: Base URL for the RSportal API (e.g., https://api.example.com)
  - `EDITOR`: Editor to use for multi-line input (falls back to Notepad on Windows)

Windows PowerShell examples:
```
$env:RSPORTAL_API_BASE = "https://api.example.com"
$env:EDITOR = "code"
```

Persist in PowerShell profile if desired.
