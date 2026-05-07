"""
main.py
-------
Entry point. Only contains GUI layout and button wiring.
All logic lives in the other modules:
  - utils.py         → date parsing
  - email_builder.py → HTML + MIME email construction
  - sender.py        → SMTP sending + CSV logging
  - preview.py       → preview window
  
HOW TO RUN (NOT inside Jupyter — use a terminal):
  Anaconda Prompt:
    cd C:\\Users\\YourName\\Documents\\email_automation
    python main.py

  VS Code:
    Open main.py → Right-click → Run Python File in Terminal

REQUIREMENTS:
  pip install pandas
  tkinter is built into Python — nothing extra needed
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import smtplib
import os
import pandas as pd
from datetime import datetime, timedelta

# ── Our own modules ───────────────────────────
from sender       import run_email_job
from email_builder import build_mime_email
from preview      import PreviewWindow


class App(tk.Tk):

    # ── Colour palette ────────────────────────
    BG     = "#0f1117"
    CARD   = "#1a1d27"
    ACCENT = "#4f8ef7"
    GREEN  = "#38c9a0"
    TEXT   = "#e8eaf0"
    MUTED  = "#6b7280"
    BORDER = "#2a2d3a"
    RED    = "#f87171"
    YELLOW = "#fbbf24"

    def __init__(self):
        super().__init__()
        self.title("Smart Email Automation  v4.0")
        self.configure(bg=self.BG)
        self.resizable(False, False)
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w, h   = 980, 780
        self.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")
        self.pdf_paths = []
        self._build()

    # ── Widget helpers ────────────────────────

    def _card(self, parent, **kw):
        return tk.Frame(parent, bg=self.CARD,
                        highlightbackground=self.BORDER,
                        highlightthickness=1, **kw)

    def _entry(self, parent, var, show=None, width=28):
        e = tk.Entry(parent, textvariable=var,
                     bg="#252836", fg=self.TEXT,
                     insertbackground=self.TEXT,
                     relief="flat", font=("Segoe UI", 10),
                     width=width, show=show or "")
        e.configure(highlightbackground=self.BORDER,
                    highlightthickness=1,
                    highlightcolor=self.ACCENT)
        return e

    def _section(self, parent, text):
        tk.Label(parent, text=text, bg=self.CARD,
                 fg=self.ACCENT,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")
        tk.Frame(parent, bg=self.BORDER,
                 height=1).pack(fill="x", pady=(3, 9))

    def _btn(self, parent, text, cmd,
             bg=None, fg="#fff", padx=10, pady=4, font_size=9):
        return tk.Button(
            parent, text=text, command=cmd,
            bg=bg or self.ACCENT, fg=fg,
            font=("Segoe UI", font_size, "bold"),
            relief="flat", cursor="hand2",
            padx=padx, pady=pady
        )

    # ── Build UI ──────────────────────────────

    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=self.BG)
        hdr.pack(fill="x", padx=28, pady=(20, 2))
        tk.Label(hdr, text="Email Automation",
                 bg=self.BG, fg=self.TEXT,
                 font=("Georgia", 22, "bold")).pack(side="left")
        tk.Label(hdr, text="v4.0",
                 bg=self.BG, fg=self.MUTED,
                 font=("Segoe UI", 9)).pack(side="left",
                                            padx=(8, 0), pady=(8, 0))
        tk.Label(self,
                 text="Fill in the form and click Send "
                      "— no code editing needed.",
                 bg=self.BG, fg=self.MUTED,
                 font=("Segoe UI", 10)).pack(anchor="w",
                                             padx=30, pady=(0, 12))

        # Three-column layout
        body = tk.Frame(self, bg=self.BG)
        body.pack(fill="x", padx=20)
        col1 = tk.Frame(body, bg=self.BG)
        col2 = tk.Frame(body, bg=self.BG)
        col3 = tk.Frame(body, bg=self.BG)
        col1.pack(side="left", fill="both", expand=True, padx=(0, 6))
        col2.pack(side="left", fill="both", expand=True, padx=6)
        col3.pack(side="left", fill="both", expand=True, padx=(6, 0))

        self._col1(col1)
        self._col2(col2)
        self._col3(col3)
        self._note_section()
        self._console_section()
        self._bottom_bar()

    # ── Column 1: CSV + PDF ───────────────────

    def _col1(self, p):
        c = self._card(p)
        c.pack(fill="x", pady=(0, 8))
        i = tk.Frame(c, bg=self.CARD)
        i.pack(fill="x", padx=14, pady=12)
        self._section(i, "CSV FILE")

        self.csv_var = tk.StringVar(value="")
        row = tk.Frame(i, bg=self.CARD)
        row.pack(fill="x", pady=(0, 8))
        tk.Label(row, textvariable=self.csv_var,
                 bg="#252836", fg=self.MUTED,
                 font=("Segoe UI", 8),
                 width=22, anchor="w").pack(side="left",
                                            ipady=5, ipadx=5)
        self._btn(row, "Browse ...",
                  self._browse_csv).pack(side="left", padx=(6, 0))

        dr = tk.Frame(i, bg=self.CARD)
        dr.pack(fill="x")
        tk.Label(dr, text="Days ahead:",
                 bg=self.CARD, fg=self.TEXT,
                 font=("Segoe UI", 10)).pack(side="left")
        self.days_var = tk.IntVar(value=3)
        tk.Spinbox(dr, from_=1, to=365,
                   textvariable=self.days_var,
                   bg="#252836", fg=self.ACCENT,
                   relief="flat",
                   font=("Segoe UI", 11, "bold"),
                   width=4, justify="center").pack(side="left", padx=6)

        c2 = self._card(p)
        c2.pack(fill="x")
        i2 = tk.Frame(c2, bg=self.CARD)
        i2.pack(fill="x", padx=14, pady=12)
        self._section(i2, "PDF ATTACHMENTS")

        btn_row = tk.Frame(i2, bg=self.CARD)
        btn_row.pack(fill="x", pady=(0, 8))
        self._btn(btn_row, "+ Add PDF",
                  self._add_pdf, bg="#2d3748").pack(side="left")
        self._btn(btn_row, "Clear All",
                  self._clear_pdfs, bg="#742a2a").pack(
            side="left", padx=(6, 0))

        self.pdf_listbox = tk.Listbox(
            i2, bg="#252836", fg=self.GREEN,
            font=("Segoe UI", 9), height=4,
            relief="flat", selectbackground=self.ACCENT,
            highlightbackground=self.BORDER,
            highlightthickness=1
        )
        self.pdf_listbox.pack(fill="x")
        tk.Label(i2,
                 text="PDFs will be attached to every email.",
                 bg=self.CARD, fg=self.MUTED,
                 font=("Segoe UI", 8)).pack(anchor="w", pady=(6, 0))

    # ── Column 2: Credentials + SMTP ─────────

    def _col2(self, p):
        c = self._card(p)
        c.pack(fill="x", pady=(0, 8))
        i = tk.Frame(c, bg=self.CARD)
        i.pack(fill="x", padx=14, pady=12)
        self._section(i, "SENDER CREDENTIALS")

        self.email_var    = tk.StringVar()
        self.password_var = tk.StringVar()

        for lbl, var, secret in [
            ("Email",        self.email_var,    False),
            ("App Password", self.password_var, True),
        ]:
            r = tk.Frame(i, bg=self.CARD)
            r.pack(fill="x", pady=4)
            tk.Label(r, text=lbl, bg=self.CARD,
                     fg=self.MUTED, font=("Segoe UI", 9),
                     width=12, anchor="w").pack(side="left")
            self._entry(r, var,
                        show="*" if secret else None,
                        width=20).pack(side="left", ipady=4)

        tk.Label(i,
                 text="Gmail App Password:\n"
                      "myaccount.google.com → Security\n"
                      "→ 2-Step → App Passwords",
                 bg=self.CARD, fg=self.MUTED,
                 font=("Segoe UI", 8),
                 justify="left").pack(anchor="w", pady=(8, 0))

        c2 = self._card(p)
        c2.pack(fill="x")
        i2 = tk.Frame(c2, bg=self.CARD)
        i2.pack(fill="x", padx=14, pady=12)
        self._section(i2, "SMTP SETTINGS")

        self.smtp_server_var = tk.StringVar(value="smtp.gmail.com")
        self.smtp_port_var   = tk.StringVar(value="587")

        for lbl, var, w in [
            ("SMTP Server", self.smtp_server_var, 18),
            ("SMTP Port",   self.smtp_port_var,    6),
        ]:
            r = tk.Frame(i2, bg=self.CARD)
            r.pack(fill="x", pady=3)
            tk.Label(r, text=lbl, bg=self.CARD,
                     fg=self.MUTED, font=("Segoe UI", 9),
                     width=12, anchor="w").pack(side="left")
            self._entry(r, var, width=w).pack(side="left", ipady=4)

        tk.Label(i2,
                 text="Gmail: smtp.gmail.com : 587\n"
                      "Outlook: smtp.office365.com : 587",
                 bg=self.CARD, fg=self.MUTED,
                 font=("Segoe UI", 8),
                 justify="left").pack(anchor="w", pady=(6, 0))

    # ── Column 3: Preview + Log ───────────────

    def _col3(self, p):
        c = self._card(p)
        c.pack(fill="x", pady=(0, 8))
        i = tk.Frame(c, bg=self.CARD)
        i.pack(fill="x", padx=14, pady=12)
        self._section(i, "PREVIEW & TEST")

        tk.Label(i,
                 text="Preview how the email will look\n"
                      "before sending to everyone.",
                 bg=self.CARD, fg=self.MUTED,
                 font=("Segoe UI", 9),
                 justify="left").pack(anchor="w", pady=(0, 10))

        self._btn(i, "Preview Email",
                  self._preview_email,
                  bg="#553c9a",
                  padx=14, pady=6,
                  font_size=10).pack(fill="x", pady=(0, 6))

        tk.Label(i,
                 text="Send a test email to yourself\n"
                      "to check formatting & attachments.",
                 bg=self.CARD, fg=self.MUTED,
                 font=("Segoe UI", 9),
                 justify="left").pack(anchor="w", pady=(6, 8))

        self._btn(i, "Send Test Email",
                  self._send_test,
                  bg="#276749",
                  padx=14, pady=6,
                  font_size=10).pack(fill="x")

        c2 = self._card(p)
        c2.pack(fill="x")
        i2 = tk.Frame(c2, bg=self.CARD)
        i2.pack(fill="x", padx=14, pady=12)
        self._section(i2, "LOG FILE")

        self.log_var = tk.StringVar(value="send_log.csv")
        r2 = tk.Frame(i2, bg=self.CARD)
        r2.pack(fill="x")
        tk.Label(r2, textvariable=self.log_var,
                 bg="#252836", fg=self.MUTED,
                 font=("Segoe UI", 8),
                 width=18, anchor="w").pack(side="left",
                                            ipady=5, ipadx=5)
        self._btn(r2, "Change ...", self._browse_log,
                  bg=self.CARD, fg=self.MUTED).pack(
            side="left", padx=(6, 0))

        tk.Label(i2,
                 text="Auto-created in the same folder.\n"
                      "Every run appends — history kept.",
                 bg=self.CARD, fg=self.MUTED,
                 font=("Segoe UI", 8),
                 justify="left").pack(anchor="w", pady=(8, 0))

    # ── Note + Console + Bottom ───────────────

    def _note_section(self):
        nc = self._card(self)
        nc.pack(fill="x", padx=20, pady=(8, 0))
        ni = tk.Frame(nc, bg=self.CARD)
        ni.pack(fill="x", padx=14, pady=10)
        self._section(ni,
                      "ADDITIONAL NOTE  "
                      "(optional — appended to every email)")
        self.note_text = tk.Text(
            ni, bg="#252836", fg=self.TEXT,
            font=("Segoe UI", 10), height=3,
            relief="flat", wrap="word",
            insertbackground=self.TEXT,
            highlightbackground=self.BORDER,
            highlightthickness=1
        )
        self.note_text.pack(fill="x")
        tk.Label(ni,
                 text="e.g.  Please bring your student ID and two pens.",
                 bg=self.CARD, fg=self.MUTED,
                 font=("Segoe UI", 8)).pack(anchor="w", pady=(4, 0))

    def _console_section(self):
        cc = self._card(self)
        cc.pack(fill="both", expand=True, padx=20, pady=(8, 6))
        hdr = tk.Frame(cc, bg=self.CARD)
        hdr.pack(fill="x", padx=12, pady=(8, 0))
        tk.Label(hdr, text="OUTPUT LOG",
                 bg=self.CARD, fg=self.ACCENT,
                 font=("Segoe UI", 9, "bold")).pack(side="left")
        tk.Button(hdr, text="Clear",
                  command=self._clear,
                  bg=self.CARD, fg=self.MUTED,
                  font=("Segoe UI", 8), relief="flat",
                  cursor="hand2").pack(side="right")

        self.console = scrolledtext.ScrolledText(
            cc, bg="#0a0c12", fg=self.TEXT,
            font=("Consolas", 10), relief="flat",
            height=8, wrap="word", state="disabled"
        )
        self.console.pack(fill="both", expand=True,
                          padx=12, pady=(4, 12))
        for tag, color in [
            ("ok",    self.GREEN),
            ("err",   self.RED),
            ("warn",  self.YELLOW),
            ("info",  self.ACCENT),
            ("plain", self.TEXT),
        ]:
            self.console.tag_configure(tag, foreground=color)

    def _bottom_bar(self):
        bar = tk.Frame(self, bg=self.BG)
        bar.pack(fill="x", padx=20, pady=(0, 14))
        self.status_var = tk.StringVar(value="Ready.")
        tk.Label(bar, textvariable=self.status_var,
                 bg=self.BG, fg=self.MUTED,
                 font=("Segoe UI", 9)).pack(side="left")
        self.send_btn = tk.Button(
            bar, text="  Send Emails  ",
            command=self._on_send,
            bg=self.ACCENT, fg="#fff",
            font=("Segoe UI", 11, "bold"),
            relief="flat", cursor="hand2",
            padx=20, pady=8
        )
        self.send_btn.pack(side="right")
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("P.Horizontal.TProgressbar",
                        troughcolor="#252836",
                        background=self.GREEN)
        self.progress = ttk.Progressbar(
            bar, mode="indeterminate", length=150,
            style="P.Horizontal.TProgressbar"
        )

    # ── Actions ───────────────────────────────

    def _browse_csv(self):
        p = filedialog.askopenfilename(
            title="Select CSV",
            filetypes=[("CSV files", "*.csv"),
                       ("All files", "*.*")]
        )
        if p:
            self.csv_var.set(p)

    def _browse_log(self):
        p = filedialog.asksaveasfilename(
            title="Save log as",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )
        if p:
            self.log_var.set(p)

    def _add_pdf(self):
        paths = filedialog.askopenfilenames(
            title="Select PDF file(s)",
            filetypes=[("PDF files", "*.pdf"),
                       ("All files", "*.*")]
        )
        for p in paths:
            if p not in self.pdf_paths:
                self.pdf_paths.append(p)
                self.pdf_listbox.insert(
                    "end", "  " + os.path.basename(p))

    def _clear_pdfs(self):
        self.pdf_paths = []
        self.pdf_listbox.delete(0, "end")

    def _clear(self):
        self.console.configure(state="normal")
        self.console.delete("1.0", "end")
        self.console.configure(state="disabled")

    def _log(self, msg):
        def _w():
            self.console.configure(state="normal")
            m   = msg.upper()
            tag = "plain"
            if "[OK]"   in m or "SUCCESS" in m: tag = "ok"
            elif "[ERROR]" in m or "FAIL" in m: tag = "err"
            elif "[TIP]"   in m or "SKIP" in m: tag = "warn"
            elif "[INFO]"  in m or "===" in m:  tag = "info"
            self.console.insert("end", msg + "\n", tag)
            self.console.see("end")
            self.console.configure(state="disabled")
        self.after(0, _w)

    def _get_note(self):
        return self.note_text.get("1.0", "end").strip()

    def _preview_email(self):
        today = datetime.today()
        PreviewWindow(
            self,
            name          = "Sample Student",
            course        = "Mathematics",
            exam_date_str = (today + timedelta(days=2)).strftime("%B %d, %Y"),
            days_label    = "in 2 days",
            urgency_color = "#2b6cb0",
            extra_note    = self._get_note(),
            pdf_paths     = self.pdf_paths,
        )

    def _send_test(self):
        email = self.email_var.get().strip()
        pwd   = self.password_var.get().strip()
        if not email or not pwd:
            messagebox.showerror(
                "Missing Credentials",
                "Please enter your email and App Password first.")
            return

        self._log("[INFO] Sending test email to yourself ...")

        def _do():
            try:
                fake = pd.Series({
                    "Name":      "Test Student",
                    "Email":     email,
                    "Course":    "Demo Course",
                    "Exam_Date": datetime.today() + timedelta(days=2),
                })
                msg = build_mime_email(
                    fake, email, self.pdf_paths, self._get_note())
                with smtplib.SMTP(
                    self.smtp_server_var.get().strip(),
                    int(self.smtp_port_var.get().strip())
                ) as server:
                    server.ehlo()
                    server.starttls()
                    server.ehlo()
                    server.login(email, pwd)
                    server.sendmail(email, email, msg.as_string())
                self._log("[OK]  Test email sent! Check your inbox.")
                self.after(0, lambda: self.status_var.set(
                    "Test email sent — check your inbox!"))
            except smtplib.SMTPAuthenticationError:
                self._log("[ERROR] Login failed — check App Password.")
            except Exception as e:
                self._log(f"[ERROR] Test email failed: {e}")

        threading.Thread(target=_do, daemon=True).start()

    def _validate(self):
        if not self.csv_var.get() or \
                not os.path.exists(self.csv_var.get()):
            messagebox.showerror("Missing CSV",
                                 "Please select a valid CSV file.")
            return False
        if not self.email_var.get().strip():
            messagebox.showerror("Missing Email",
                                 "Please enter your sender email.")
            return False
        if not self.password_var.get().strip():
            messagebox.showerror("Missing Password",
                                 "Please enter your App Password.")
            return False
        return True

    def _on_send(self):
        if not self._validate():
            return
        self._clear()
        self.send_btn.configure(state="disabled",
                                text="  Sending ...")
        self.status_var.set("Sending emails ...")
        self.progress.pack(side="right", padx=(0, 10))
        self.progress.start(12)
        threading.Thread(target=self._thread, daemon=True).start()

    def _thread(self):
        ok = run_email_job(
            csv_path        = self.csv_var.get(),
            sender_email    = self.email_var.get().strip(),
            sender_password = self.password_var.get().strip(),
            smtp_server     = self.smtp_server_var.get().strip(),
            smtp_port       = self.smtp_port_var.get().strip(),
            days_ahead      = self.days_var.get(),
            log_path        = self.log_var.get(),
            pdf_paths       = self.pdf_paths,
            extra_note      = self._get_note(),
            log_callback    = self._log,
        )
        self.after(0, self._done, ok)

    def _done(self, ok):
        self.progress.stop()
        self.progress.pack_forget()
        self.send_btn.configure(state="normal",
                                text="  Send Emails  ")
        self.status_var.set(
            "Done! Check the log above." if ok
            else "Finished with issues — see log above."
        )


# ── Entry point ───────────────────────────────

if __name__ == "__main__":
    App().mainloop()
