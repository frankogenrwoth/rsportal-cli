import tkinter as tk
from tkinter import ttk, messagebox
import requests
from utils import get_api_base
from rsportal import storage_sqlite


class AuthDialog(tk.Toplevel):
    def __init__(self, parent, on_success=None):
        super().__init__(parent)
        self.parent = parent
        self.on_success = on_success
        self.title("Login")
        self.geometry("360x160")
        self.transient(parent)
        self.grab_set()

        frm = ttk.Frame(self, padding=12)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="Username:").grid(row=0, column=0, sticky="w")
        self.user_entry = ttk.Entry(frm)
        self.user_entry.grid(row=0, column=1, sticky="ew")

        ttk.Label(frm, text="Password:").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.pw_entry = ttk.Entry(frm, show="*")
        self.pw_entry.grid(row=1, column=1, sticky="ew", pady=(8, 0))

        frm.columnconfigure(1, weight=1)

        btn_frame = ttk.Frame(frm)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=(12, 0))
        login_btn = ttk.Button(btn_frame, text="Login", command=self.attempt_login)
        login_btn.pack(side="left")
        cancel_btn = ttk.Button(btn_frame, text="Cancel", command=self.close)
        cancel_btn.pack(side="left", padx=(8, 0))

        # pre-fill if saved
        saved = storage_sqlite.get_saved_auth()
        if saved:
            self.user_entry.insert(0, saved.get("username") or "")

    def close(self):
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()

    def attempt_login(self):
        username = self.user_entry.get().strip()
        password = self.pw_entry.get().strip()
        if not username or not password:
            messagebox.showwarning("Missing", "Please enter username and password")
            return
        base = get_api_base()
        url = f"{base}/auth/check"
        try:
            resp = requests.get(url, auth=(username, password), timeout=10)
            if resp.status_code in (200, 204):
                # save into sqlite; do not overwrite existing active auth unless user logs out explicitly
                saved_ok = storage_sqlite.save_auth(username, password, force=False)
                if not saved_ok:
                    messagebox.showinfo("Already logged in", "An active credential already exists. Please logout first if you want to replace it.")
                    return
                messagebox.showinfo("Success", "Logged in and credentials saved locally.")
                if callable(self.on_success):
                    self.on_success()
                self.close()
                return
        except Exception as e:
            messagebox.showerror("Error", f"Failed to verify credentials: {e}")
            return
        messagebox.showerror("Invalid", "Invalid credentials or server did not accept the login.")
