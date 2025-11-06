import json
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import threading
import time
from datetime import datetime, timedelta, timezone
from rsportal import storage_sqlite


tz = timezone(timedelta(hours=3, minutes=0))  # UTC+3 (Uganda, kampala)


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

        # Time entries tab - show as a table (Treeview) with columns: Start, End, Duration, Notes
        te_frame = ttk.Frame(tabs)
        tabs.add(te_frame, text="Time Entries")
        cols = ("synced", "start", "end", "duration", "notes")
        self.te_tree = ttk.Treeview(
            te_frame, columns=cols, show="headings", selectmode="browse"
        )
        self.te_tree.heading("synced", text="Synced")
        self.te_tree.heading("start", text="Start")
        self.te_tree.heading("end", text="End")
        self.te_tree.heading("duration", text="Duration")
        self.te_tree.heading("notes", text="Notes")
        self.te_tree.column("synced", width=80, anchor="center")
        self.te_tree.column("start", width=160, anchor="w")
        self.te_tree.column("end", width=160, anchor="w")
        self.te_tree.column("duration", width=120, anchor="center")
        self.te_tree.column("notes", width=240, anchor="w")
        vsb = ttk.Scrollbar(te_frame, orient="vertical", command=self.te_tree.yview)
        self.te_tree.configure(yscroll=vsb.set)
        self.te_tree.pack(fill="both", expand=True, side="left", padx=8, pady=8)
        vsb.pack(fill="y", side="right", pady=8)

        # Comments tab
        cm_frame = ttk.Frame(tabs)
        tabs.add(cm_frame, text="Comments")

        self.comments_canvas = tk.Canvas(
            cm_frame, borderwidth=0, highlightthickness=0, height=200
        )
        self.comments_container = ttk.Frame(self.comments_canvas)
        self.comments_window = self.comments_canvas.create_window(
            (0, 0), window=self.comments_container, anchor="nw"
        )

        self.comments_vsb = ttk.Scrollbar(
            cm_frame, orient="vertical", command=self.comments_canvas.yview
        )
        self.comments_canvas.configure(yscrollcommand=self.comments_vsb.set)
        self.comments_vsb.pack(side="right", fill="y", padx=(0, 4))
        self.comments_canvas.pack(fill="both", expand=True, padx=8, pady=(8, 4))

        def _on_container_config(event):
            try:
                self.comments_canvas.configure(
                    scrollregion=self.comments_canvas.bbox("all")
                )
            except Exception:
                pass

        def _on_canvas_config(event):
            try:
                self.comments_canvas.itemconfig(self.comments_window, width=event.width)
            except Exception:
                pass

        self.comments_container.bind("<Configure>", _on_container_config)
        self.comments_canvas.bind("<Configure>", _on_canvas_config)

        # Input area: comment Text and Add button close together at the bottom
        input_frame = ttk.Frame(cm_frame)
        input_frame.pack(fill="x", padx=8, pady=(4, 8))

        self.comment_txt = tk.Text(input_frame, height=4)
        self.comment_txt.pack(side="left", fill="x", expand=True)

        add_c_btn = ttk.Button(
            input_frame, text="Add Comment", command=self.add_comment
        )
        add_c_btn.pack(side="right", padx=(8, 0))

        # Load and render existing comments
        self.load_comments()

        documentation_frame = ttk.Frame(tabs)
        tabs.add(documentation_frame, text="Documentation")

        # --- Documentation form (saved to docs/) ---
        # We'll create a scrollable form similar to comments UI because it's long
        self.docs_canvas = tk.Canvas(
            documentation_frame, borderwidth=0, highlightthickness=0, height=300
        )
        self.docs_container = ttk.Frame(self.docs_canvas)
        self.docs_window = self.docs_canvas.create_window(
            (0, 0), window=self.docs_container, anchor="nw"
        )

        self.docs_vsb = ttk.Scrollbar(
            documentation_frame, orient="vertical", command=self.docs_canvas.yview
        )
        self.docs_canvas.configure(yscrollcommand=self.docs_vsb.set)
        self.docs_vsb.pack(side="right", fill="y", padx=(0, 4))
        self.docs_canvas.pack(fill="both", expand=True, padx=8, pady=(8, 4))

        def _on_docs_container_config(event):
            try:
                self.docs_canvas.configure(scrollregion=self.docs_canvas.bbox("all"))
            except Exception:
                pass

        def _on_docs_canvas_config(event):
            try:
                self.docs_canvas.itemconfig(self.docs_window, width=event.width)
            except Exception:
                pass

        self.docs_container.bind("<Configure>", _on_docs_container_config)
        self.docs_canvas.bind("<Configure>", _on_docs_canvas_config)

        # Form fields
        self.doc_fields = {}

        def add_text_field(key, label_text, hint=None, rows=4):
            frame = ttk.Frame(self.docs_container)
            frame.pack(fill="x", pady=6, padx=8)
            lbl = ttk.Label(frame, text=label_text)
            lbl.pack(anchor="w")
            txt = tk.Text(frame, height=rows)
            txt.pack(fill="x", pady=(4, 0))
            if hint:
                hint_lbl = ttk.Label(frame, text=hint, font=(None, 8))
                hint_lbl.pack(anchor="w", pady=(2, 0))
            self.doc_fields[key] = txt

        def add_entry_field(key, label_text, hint=None):
            frame = ttk.Frame(self.docs_container)
            frame.pack(fill="x", pady=6, padx=8)
            lbl = ttk.Label(frame, text=label_text)
            lbl.pack(anchor="w")
            ent = ttk.Entry(frame)
            ent.pack(fill="x", pady=(4, 0))
            if hint:
                hint_lbl = ttk.Label(frame, text=hint, font=(None, 8))
                hint_lbl.pack(anchor="w", pady=(2, 0))
            self.doc_fields[key] = ent

        # Mirror fields from the provided HTML
        add_text_field(
            "objective",
            "Objective (Diagnosis)",
            "What’s the goal/problem?",
            rows=4,
        )
        add_text_field(
            "summary",
            "Summary (Treatment Outcome)",
            "1–3 sentences describing what was done + result.",
            rows=4,
        )
        add_text_field(
            "key_files_modules_modified",
            "Key Files / Modules Modified",
            "List repos, files, or modules changed",
            rows=4,
        )
        add_text_field(
            "functions_classes_endpoints",
            "Functions / Classes / Endpoints",
            "Details on specific code changes and their purpose",
            rows=4,
        )
        add_text_field(
            "architectural_structural_changes",
            "Architectural / Structural Changes",
            "e.g., Database schema, API design, etc.",
            rows=4,
        )
        add_entry_field(
            "git_commits_pr_links",
            "Git Commits / PR Links",
            "Provide direct links to commits or pull requests",
        )
        add_text_field(
            "data_flow_integrations",
            "Data Flow / Integrations",
            "Explain how data moves across systems",
            rows=4,
        )
        add_text_field(
            "testing_validation_steps",
            "Testing / Validation Steps",
            "e.g., Unit tests, API calls, logs to check",
            rows=4,
        )
        add_text_field(
            "expected_result",
            "Expected Result",
            "Conditions for a successful run",
            rows=4,
        )
        add_text_field(
            "impact_on_other_systems",
            "Impact on Other Systems",
            "Dependencies that were affected",
            rows=4,
        )
        add_text_field(
            "handoff_notes",
            "Handoff Notes",
            "What the next developer should know",
            rows=4,
        )
        add_text_field(
            "supporting_media",
            "Supporting Media",
            "Links to diagrams, screenshots, logs",
            rows=4,
        )

        # Buttons: Save and Reload
        btn_frame = ttk.Frame(self.docs_container)
        btn_frame.pack(fill="x", pady=8, padx=8)
        save_btn = ttk.Button(
            btn_frame,
            text="Save Documentation",
            command=lambda: self.save_documentation(),
        )
        save_btn.pack(side="right", padx=(8, 0))
        reload_btn = ttk.Button(
            btn_frame, text="Reload", command=lambda: self.load_documentation()
        )
        reload_btn.pack(side="right")

        # Initialize docs file path details
        self._docs_dir = Path(__file__).resolve().parents[2] / "docs"
        # ensure docs dir exists
        try:
            self._docs_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

        # load existing documentation for this task (if present)
        try:
            self.load_documentation()
        except Exception:
            pass

        self._timer_running = False
        self._timer_start_ts = None
        self._timer_thread = None

        self.load_time_entries()

    def load_time_entries(self):
        # Populate the Treeview with time entries from sqlite
        # Clear existing
        for iid in list(self.te_tree.get_children()):
            self.te_tree.delete(iid)
        entries = storage_sqlite.get_time_entries(self.task_id)
        for e in entries:
            start = e.get("start_time")
            end = e.get("end_time")
            dur = "-"
            start_fmt = ""
            end_fmt = ""
            if start:
                try:
                    s = datetime.fromisoformat(start.replace("Z", ""))
                    start_fmt = s.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    start_fmt = start
            if end:
                try:
                    en = datetime.fromisoformat(end.replace("Z", ""))
                    end_fmt = en.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    end_fmt = end
            else:
                end_fmt = "running"

            if start and end:
                try:
                    s = datetime.fromisoformat(start.replace("Z", ""))
                    en = datetime.fromisoformat(end.replace("Z", ""))
                    dd = en - s
                    # format duration as H:MM or X days, H:MM:SS when long
                    if dd.days:
                        dur = str(dd)
                    else:
                        hrs = int(dd.total_seconds() // 3600)
                        mins = int((dd.total_seconds() % 3600) // 60)
                        dur = f"{hrs}h {mins}m"
                except Exception:
                    dur = f"{start} -> {end}"

            notes = e.get("notes") or ""
            synced = "online" if e.get("synced") == 1 else "offline"
            iid = str(e.get("id") or f"row-{len(entries)}")
            self.te_tree.insert(
                "", "end", iid=iid, values=(synced, start_fmt, end_fmt, dur, notes)
            )

    def load_comments(self):
        """Load comments from sqlite and render them in the comments container.
        Comments authored by the current saved user appear on the right, others on the left.
        """
        # clear existing widgets
        for child in list(self.comments_container.winfo_children()):
            child.destroy()

        # get saved username if available
        saved = storage_sqlite.get_saved_auth()
        saved_username = saved.get("username") if saved else None

        try:
            conn = storage_sqlite._conn()
            cur = conn.cursor()
            cur.execute(
                "SELECT id, author, comment, created_at FROM comments WHERE task_id = ? ORDER BY created_at ASC",
                (self.task_id,),
            )
            rows = cur.fetchall()
            conn.close()
        except Exception:
            rows = []

        for r in rows:
            # r may be sqlite3.Row or tuple
            if hasattr(r, "keys"):
                author = r[1]
                comment = r[2]
                created = r[3]
            else:
                author = r[1]
                comment = r[2]
                created = r[3]

            is_me = False
            if author is None and saved_username is None:
                is_me = True
            elif saved_username and author == saved_username:
                is_me = True

            # container for single comment
            row_frame = ttk.Frame(self.comments_container)
            # visual bubble
            bubble = tk.Label(
                row_frame,
                text=comment,
                justify="left",
                wraplength=420,
                bg="#e6f0ff" if is_me else "#f0f0f0",
                relief="groove",
                padx=8,
                pady=6,
            )
            meta = ttk.Label(
                row_frame, text=(f"{author or 'me'} • {created}"), font=(None, 8)
            )

            if is_me:
                # pack to right
                row_frame.pack(fill="x", pady=4, padx=8)
                bubble.pack(side="right", anchor="e")
                meta.pack(side="right", anchor="e", pady=(2, 0))
            else:
                row_frame.pack(fill="x", pady=4, padx=8)
                bubble.pack(side="left", anchor="w")
                meta.pack(side="left", anchor="w", pady=(2, 0))

        # scroll to bottom
        try:
            self.comments_canvas.update_idletasks()
            self.comments_canvas.yview_moveto(1.0)
        except Exception:
            pass

    def save_documentation(self):
        """saving documentation writes the json data to the sqlite db"""

        """Collect fields and save a JSON and a markdown copy under docs/"""
        data = {}
        for key, widget in self.doc_fields.items():
            try:
                if isinstance(widget, tk.Text):
                    val = widget.get("1.0", tk.END).strip()
                else:
                    val = widget.get().strip()
            except Exception:
                try:
                    val = widget.get().strip()
                except Exception:
                    val = ""
            data[key] = val

        try:
            conn_id = storage_sqlite._conn()
            cur = conn_id.cursor()
            cur.execute(
                "UPDATE tasks SET documentation = ? WHERE id = ?",
                (json.dumps(data, indent=2), self.task_id),
            )
            conn_id.commit()
            conn_id.close()

            messagebox.showinfo("Saved", f"Documentation saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", "Failed to save documentation")

    def load_documentation(self):
        """reload the documentation from the database."""
        try:
            conn_id = storage_sqlite._conn()
            cur = conn_id.cursor()
            cur.execute(
                "SELECT documentation, author FROM tasks WHERE id = ?",
                (self.task_id,),
            )
            row = cur.fetchone()
            doc_json = row[0] if row else None

            conn_id.commit()
            conn_id.close()

        except Exception:
            doc_json = None
            pass

        docs = json.loads(doc_json) if doc_json else {}

        for key, widget in self.doc_fields.items():
            val = docs.get(key, "")
            try:
                if isinstance(widget, tk.Text):
                    widget.delete("1.0", tk.END)
                    widget.insert("1.0", val)
                else:
                    widget.delete(0, tk.END)
                    widget.insert(0, val)
            except Exception:
                pass

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
            # prefer to save the active username when available
            saved = storage_sqlite.get_saved_auth()
            author = saved.get("username") if saved else None
            conn_id = storage_sqlite._conn()
            cur = conn_id.cursor()
            cur.execute(
                "INSERT INTO comments (task_id, author, comment) VALUES (?, ?, ?)",
                (self.task_id, author, txt),
            )
            conn_id.commit()
            conn_id.close()
            self.comment_txt.delete("1.0", tk.END)
            messagebox.showinfo("Saved", "Comment saved locally.")
            # refresh comment list
            try:
                self.load_comments()
            except Exception:
                pass
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save comment: {e}")

    def toggle_timer(self):
        if not self._timer_running:
            # start
            self._timer_start_ts = datetime.now(tz).isoformat() + "Z"
            storage_sqlite.save_time_entry(
                self.task_id, self._timer_start_ts, None, "Started from GUI"
            )
            self._timer_running = True
            self.timer_btn.config(text="Stop")
            self._timer_thread = threading.Thread(target=self._tick_loop, daemon=True)
            self._timer_thread.start()

        else:
            # stop last running entry for this task
            now = datetime.now(tz).isoformat() + "Z"
            self.stop_entry_with_dialog(now)

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
                    elapsed = datetime.now(tz) - s
                    hrs = int(elapsed.total_seconds() // 3600)
                    mins = int((elapsed.total_seconds() % 3600) // 60)
                    secs = int(elapsed.total_seconds() % 60)
                    self.elapsed_lbl.config(text=f"{hrs:02d}:{mins:02d}:{secs:02d}")
                else:
                    self.elapsed_lbl.config(text="00:00:00")
            except Exception:
                pass
            time.sleep(1)

    def stop_entry_with_dialog(self, now_iso: str):
        """Show a modal dialog when stopping the running timer to collect notes and
        an hours/minutes adjustment. Compute start_time = now - (hours,minutes) and
        update the DB row for the running entry.
        """
        # find running entry
        entries = storage_sqlite.get_time_entries(self.task_id)
        running = None
        for e in entries:
            if not e.get("end_time"):
                running = e
                break
        if not running:
            messagebox.showinfo("No running entry", "No running time entry to stop.")
            return

        # prepare defaults
        now_dt = datetime.fromisoformat(now_iso.replace("Z", ""))
        default_h = 0
        default_m = 0
        if running.get("start_time"):
            try:
                s = datetime.fromisoformat(running.get("start_time").replace("Z", ""))
                delta = now_dt - s
                default_h = int(delta.total_seconds() // 3600)
                default_m = int((delta.total_seconds() % 3600) // 60)
                default_s = int(delta.total_seconds() % 60)
            except Exception:
                default_h = 0
                default_m = 0
                default_s = 0

        dlg = tk.Toplevel(self)
        dlg.title("Stop timer")
        dlg.transient(self)
        dlg.grab_set()

        ttk.Label(dlg, text=f"Stop time: {now_dt.strftime('%Y-%m-%d %H:%M')}").grid(
            row=0, column=0, columnspan=4, pady=(8, 4), padx=8
        )

        ttk.Label(dlg, text="Hours:").grid(row=1, column=0, sticky="e", padx=(8, 4))
        hours_var = tk.IntVar(value=default_h)
        hours_spin = ttk.Spinbox(dlg, from_=0, to=999, textvariable=hours_var, width=6)
        hours_spin.grid(row=1, column=1, sticky="w")

        ttk.Label(dlg, text="Minutes:").grid(row=1, column=2, sticky="e", padx=(8, 4))
        mins_var = tk.IntVar(value=default_m)
        mins_spin = ttk.Spinbox(dlg, from_=0, to=59, textvariable=mins_var, width=6)
        mins_spin.grid(row=1, column=2, sticky="w")

        ttk.Label(dlg, text="Seconds:").grid(row=1, column=2, sticky="e", padx=(8, 4))
        secs_var = tk.IntVar(value=default_s)
        secs_spin = ttk.Spinbox(dlg, from_=0, to=59, textvariable=secs_var, width=6)
        secs_spin.grid(row=1, column=3, sticky="w")

        ttk.Label(dlg, text="Notes:").grid(
            row=2, column=0, sticky="nw", padx=8, pady=(8, 0)
        )
        notes_txt = tk.Text(dlg, width=50, height=6)
        notes_txt.grid(row=2, column=1, columnspan=3, padx=8, pady=(8, 0))
        notes_txt.insert("1.0", running.get("notes") or "")

        def do_save():
            h = hours_var.get()
            m = mins_var.get()
            s = secs_var.get()
            # ensure minutes within 0-59
            try:
                m = int(m) % 60

            except Exception:
                m = 0
                s = 0
            start_dt = now_dt - timedelta(hours=int(h), minutes=int(m), seconds=int(s))
            start_iso = start_dt.isoformat() + "Z"
            notes = notes_txt.get("1.0", tk.END).strip()
            try:
                conn = storage_sqlite._conn()
                cur = conn.cursor()
                cur.execute(
                    "UPDATE time_entries SET end_time = ?, start_time = ?, notes = ? WHERE id = ?",
                    (now_iso, start_iso, notes, running.get("id")),
                )
                conn.commit()
                conn.close()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save time entry: {e}")
            finally:
                dlg.grab_release()
                dlg.destroy()
                self._timer_running = False
                self.timer_btn.config(text="Start")
                self.load_time_entries()

        def do_cancel():
            dlg.grab_release()
            dlg.destroy()

        btn_frame = ttk.Frame(dlg)
        btn_frame.grid(row=3, column=0, columnspan=4, pady=8)
        ttk.Button(btn_frame, text="Save", command=do_save).pack(side="right", padx=8)
        ttk.Button(btn_frame, text="Cancel", command=do_cancel).pack(side="right")

    def on_close(self):
        # if timer running, stop and record now
        if self._timer_running:
            self.toggle_timer()
        self.destroy()
