import json
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from datetime import datetime
from rsportal import storage_sqlite


class TaskDetailWindow(tk.Toplevel):
    def __init__(self, master, task_id: str):
        super().__init__(master)
        self.task_id = str(task_id)
        self.title(f"Task: {self.task_id}")
        self.geometry("700x500")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.task = storage_sqlite.get_task(self.task_id) or {
            "id": self.task_id,
            "title": "",
        }

        header = ttk.Frame(self)
        header.pack(fill="both", padx=8, pady=8)

        # Stack labels vertically and left-align them
        ttk.Label(
            header,
            text=self.task.get("title") or "(no title)",
            font=(None, 14, "bold"),
        ).pack(side="left", anchor="w")

        self.timer_btn = ttk.Button(header, text="Start", command=self.toggle_timer)
        self.timer_btn.pack(side="right")
        self.elapsed_lbl = ttk.Label(header, text="00:00:00")
        self.elapsed_lbl.pack(side="right", padx=8)

        # Tabs
        tabs = ttk.Notebook(self)
        tabs.pack(fill="both", expand=True, padx=8, pady=8)

        # Details tab
        details = ttk.Frame(tabs)
        tabs.add(details, text="Details")

        ttk.Label(
            details,
            text=f"Assignee: {json.loads(self.task.get('assignee')).get('username') or '(unassigned)'}",
        ).pack(anchor="w", pady=(4, 0))
        ttk.Label(
            details,
            text=f"Assigner: {json.loads(self.task.get('assigner')).get('username') or 'unknown'}",
        ).pack(anchor="w", pady=(2, 0))
        ttk.Label(
            details,
            text=f"Project: {json.loads(self.task.get('project')).get('name') or ''}",
        ).pack(anchor="w", pady=(2, 0))
        ttk.Label(
            details,
            text=f"Category: {self.task.get('category') or 'general'}",
        ).pack(anchor="w", pady=(2, 0))
        ttk.Label(
            details,
            text=f"Urgency: {self.task.get('urgency') or 'normal'}",
        ).pack(anchor="w", pady=(2, 0))
        ttk.Label(
            details,
            text=f"Deadline: {self.task.get('deadline') or 'none'}",
        ).pack(anchor="w", pady=(2, 0))

        status_options = [
            "TODO",
            "IN_PROGRESS",
            "BLOCKED",
            "PM_REVIEW",
            "CTO_REVIEW",
            "COMPLETED",
        ]

        self.status_frame = ttk.Frame(details)
        self.status_frame.pack(anchor="w", pady=(2, 0))
        ttk.Label(
            self.status_frame,
            text=f"Status: ",
        ).pack(side="left", pady=(2, 0))

        self.status_cb = ttk.Combobox(
            self.status_frame,
            values=status_options,
            state="readonly",
            width=16,
        )
        # set initial value explicitly
        self.status_cb.set(self.task.get("status") or "TODO")
        self.status_cb.pack(side="right", pady=(2, 8))
        # Persist status changes when user picks a new value
        self.status_cb.bind("<<ComboboxSelected>>", self.on_status_change)

        # Time entries tab
        te_frame = ttk.Frame(tabs)
        tabs.add(te_frame, text="Time Entries")
        self.te_list = tk.Listbox(te_frame)
        self.te_list.pack(fill="both", expand=True, padx=8, pady=8)

        # Comments tab
        cm_frame = ttk.Frame(tabs)
        tabs.add(cm_frame, text="Comments")
        self.comment_txt = tk.Text(cm_frame, height=5)
        self.comment_txt.pack(fill="x", padx=8, pady=8)
        add_c_btn = ttk.Button(cm_frame, text="Add Comment", command=self.add_comment)
        add_c_btn.pack(padx=8, pady=4)

        documentation_frame = ttk.Frame(tabs)
        tabs.add(documentation_frame, text="Documentation")

        self._timer_running = False
        self._timer_start_ts = None
        self._timer_thread = None

        self.load_time_entries()

    def load_time_entries(self):
        self.te_list.delete(0, tk.END)
        entries = storage_sqlite.get_time_entries(self.task_id)
        for e in entries:
            start = e.get("start_time")
            end = e.get("end_time")
            dur = "-"
            if start and end:
                try:
                    s = datetime.fromisoformat(start.replace("Z", ""))
                    en = datetime.fromisoformat(end.replace("Z", ""))
                    dd = en - s
                    dur = str(dd)
                except Exception:
                    dur = f"{start} -> {end}"
            self.te_list.insert(tk.END, f"{start} - {end or 'running'} ({dur})")
        
    def on_status_change(self, event=None):
        """Handler called when the status combobox value changes. Update local task
        dict and persist to sqlite using storage_sqlite.upsert_tasks.
        """
        new_status = self.status_cb.get()
        self.task["status"] = new_status
        try:
            storage_sqlite.upsert_tasks([self.task])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save status: {e}")

    def add_comment(self):
        txt = self.comment_txt.get("1.0", tk.END).strip()
        if not txt:
            messagebox.showinfo("Empty", "Please enter a comment first.")
            return
        # save to sqlite comments table
        try:
            conn_id = storage_sqlite._conn()
            cur = conn_id.cursor()
            cur.execute(
                "INSERT INTO comments (task_id, author, comment) VALUES (?, ?, ?)",
                (self.task_id, None, txt),
            )
            conn_id.commit()
            conn_id.close()
            self.comment_txt.delete("1.0", tk.END)
            messagebox.showinfo("Saved", "Comment saved locally.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save comment: {e}")

    def toggle_timer(self):
        if not self._timer_running:
            # start
            self._timer_start_ts = datetime.utcnow().isoformat() + "Z"
            storage_sqlite.save_time_entry(
                self.task_id, self._timer_start_ts, None, "Started from GUI"
            )
            self._timer_running = True
            self.timer_btn.config(text="Stop")
            self._timer_thread = threading.Thread(target=self._tick_loop, daemon=True)
            self._timer_thread.start()
        else:
            # stop last running entry for this task
            now = datetime.utcnow().isoformat() + "Z"
            # update latest entry with null end_time
            conn = storage_sqlite._conn()
            cur = conn.cursor()
            cur.execute(
                "UPDATE time_entries SET end_time = ? WHERE task_id = ? AND end_time IS NULL",
                (now, self.task_id),
            )
            conn.commit()
            conn.close()
            self._timer_running = False
            self.timer_btn.config(text="Start")
            self.load_time_entries()

    def _tick_loop(self):
        while self._timer_running:
            # compute elapsed from last running entry start
            try:
                entries = storage_sqlite.get_time_entries(self.task_id)
                # find first entry with end_time is None
                running = None
                for e in entries:
                    if not e.get("end_time"):
                        running = e
                        break
                if running:
                    s = datetime.fromisoformat(
                        running.get("start_time").replace("Z", "")
                    )
                    elapsed = datetime.utcnow() - s
                    hrs = int(elapsed.total_seconds() // 3600)
                    mins = int((elapsed.total_seconds() % 3600) // 60)
                    secs = int(elapsed.total_seconds() % 60)
                    self.elapsed_lbl.config(text=f"{hrs:02d}:{mins:02d}:{secs:02d}")
                else:
                    self.elapsed_lbl.config(text="00:00:00")
            except Exception:
                pass
            time.sleep(1)

    def on_close(self):
        # if timer running, stop and record now
        if self._timer_running:
            self.toggle_timer()
        self.destroy()
