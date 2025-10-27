import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

# Ensure project root is on sys.path so absolute imports work when running this file directly
_HERE = Path(__file__).resolve()
_PROJECT_ROOT = str(_HERE.parents[2])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from rsportal.gui.home_view import HomeView
from rsportal import storage_sqlite
from utils import is_authenticated


def run_app():
    storage_sqlite.init_db()

    root = tk.Tk()
    root.title("RSportal — Tasks")
    root.geometry("900x600")

    if not is_authenticated():
        messagebox.showinfo(
            "Authentication",
            "No active authenticated user found. Please run 'rsportal auth --login' in the terminal or use the CLI to authenticate.\n\nGUI will continue in offline mode.",
        )

    container = ttk.Frame(root)
    container.pack(fill="both", expand=True)

    app = HomeView(container, root)
    app.pack(fill="both", expand=True)

    # on close: ensure running timers are stopped
    def on_close():
        # stop any running entries by setting end_time to now
        try:
            storage_sqlite.stop_running_entries_and_get()
        except Exception:
            pass
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


if __name__ == "__main__":
    run_app()
