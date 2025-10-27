import threading
import tkinter as tk
from tkinter import ttk, messagebox
from rsportal import storage_sqlite
from .detail_view import TaskDetailWindow


class HomeView(ttk.Frame):
    def __init__(self, parent, root):
        super().__init__(parent)
        self.root = root
        self.filter_var = tk.StringVar(value="ALL")

        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=8, pady=6)

        refresh_btn = ttk.Button(toolbar, text="Refresh", command=self.refresh)
        refresh_btn.pack(side="left")

        sync_btn = ttk.Button(toolbar, text="Sync", command=self.sync_remote)
        sync_btn.pack(side="left", padx=(6, 0))

        ttk.Label(toolbar, text="Status:").pack(side="left", padx=(8, 4))
        self.status_combo = ttk.Combobox(
            toolbar,
            values=["ALL", "TODO", "IN_PROGRESS", "DONE", "PM_REVIEW", "CTO_REVIEW"],
            textvariable=self.filter_var,
            state="readonly",
            width=14,
        )
        self.status_combo.pack(side="left")
        self.status_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        open_btn = ttk.Button(toolbar, text="Open", command=self.open_selected)
        open_btn.pack(side="right")

        # Treeview
        cols = ("id", "title", "status", "deadline")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c.title())
            self.tree.column(c, width=200 if c == "title" else 120)
        self.tree.pack(fill="both", expand=True, padx=8, pady=8)
        self.tree.bind("<Double-1>", lambda e: self.open_selected())

        # Initial load
        self.refresh()

    def refresh(self):
        # Refresh view from local sqlite cache (no remote network call)
        status = self.filter_var.get()
        tasks = storage_sqlite.get_tasks(status=status if status != "ALL" else None)
        # clear
        for i in self.tree.get_children():
            self.tree.delete(i)
        for t in tasks:
            self.tree.insert(
                "",
                "end",
                values=(
                    t.get("id"),
                    t.get("title"),
                    t.get("status"),
                    t.get("deadline"),
                ),
            )

    def _set_toolbar_state(self, enabled: bool):
        # disable/enable buttons and combobox in the toolbar
        try:
            for child in self.winfo_children():
                if isinstance(child, ttk.Frame):
                    for w in child.winfo_children():
                        try:
                            w.config(state=("normal" if enabled else "disabled"))
                        except Exception:
                            pass
        except Exception:
            pass

    def sync_remote(self):
        # Run remote refresh in a background thread to avoid blocking UI
        def _worker():
            self._set_toolbar_state(False)
            try:
                count = storage_sqlite.refresh_tasks_from_remote()
                err = None
            except Exception as e:
                count = 0
                err = e

            def _done():
                self._set_toolbar_state(True)
                self.refresh()
                if err:
                    messagebox.showerror("Sync Failed", f"Failed to sync: {err}")
                else:
                    messagebox.showinfo("Synced", f"Pulled {count} tasks from server.")

            try:
                self.root.after(0, _done)
            except Exception:
                pass

        threading.Thread(target=_worker, daemon=True).start()

    def open_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Please select a task to open.")
            return
        item = self.tree.item(sel[0])
        task_id = item.get("values")[0]
        TaskDetailWindow(self.root, task_id)
