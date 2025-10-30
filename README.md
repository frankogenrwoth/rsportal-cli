## RSportal (GUI)
RSportal is a graphical desktop application for interacting with the RSportal platform offline-first.

Project layout (top-level):

rsportal/
├─ rsportal/
│  ├─ __init__.py
│  ├─ gui/
│  │  ├─ app.py        ← GUI entry and application bootstrap
│  │  ├─ auth_dialog.py
│  │  ├─ home_view.py
│  │  └─ ...
│  ├─ storage_sqlite.py
│  ├─ storage.py
│  └─ commands/        ← legacy command handlers (kept for reference)
├─ pyproject.toml
└─ main.py             ← entry script (now launches GUI)

