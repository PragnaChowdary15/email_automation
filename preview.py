"""
preview.py
----------
Standalone tkinter preview window.
Shows exactly how the email will look to the recipient.
"""

import os
import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta


class PreviewWindow(tk.Toplevel):
    """
    Opens as a child window on top of the main App.
    Usage:
        PreviewWindow(parent, name, course, exam_date_str,
                      days_label, urgency_color, extra_note, pdf_paths)
    """

    BG    = "#ffffff"
    DARK  = "#1a1d27"
    BLUE  = "#1a365d"
    LBLUE = "#2b6cb0"
    GRAY  = "#718096"
    TEXT  = "#2d3748"
    LIGHT = "#f4f6f9"

    def __init__(self, parent, name, course, exam_date_str,
                 days_label, urgency_color, extra_note, pdf_paths):
        super().__init__(parent)
        self.title("Email Preview")
        self.configure(bg=self.BG)
        self.resizable(True, True)

        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w, h   = 640, 700
        self.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

        self._build(name, course, exam_date_str,
                    days_label, urgency_color, extra_note, pdf_paths)

    def _build(self, name, course, exam_date_str,
               days_label, urgency_color, extra_note, pdf_paths):

        # ── Top bar ───────────────────────────────────────────────
        top = tk.Frame(self, bg=self.DARK, pady=10)
        top.pack(fill="x")
        tk.Label(top, text="Email Preview",
                 bg=self.DARK, fg="#e8eaf0",
                 font=("Segoe UI", 13, "bold")).pack(side="left", padx=16)
        tk.Label(top,
                 text="This is how your email will look to recipients.",
                 bg=self.DARK, fg="#6b7280",
                 font=("Segoe UI", 9)).pack(side="left")
        tk.Button(top, text="Close",
                  command=self.destroy,
                  bg="#e53e3e", fg="#fff",
                  font=("Segoe UI", 9, "bold"),
                  relief="flat", padx=12,
                  cursor="hand2").pack(side="right", padx=12)

        # ── Subject bar ───────────────────────────────────────────
        subj = tk.Frame(self, bg="#edf2f7", pady=8)
        subj.pack(fill="x")
        tk.Label(subj,
                 text=f"Subject:  Exam Reminder: {course} "
                      f"is {days_label} — {exam_date_str}",
                 bg="#edf2f7", fg=self.TEXT,
                 font=("Segoe UI", 9, "bold"),
                 anchor="w").pack(padx=16, fill="x")

        # ── Scrollable canvas ─────────────────────────────────────
        canvas = tk.Canvas(self, bg=self.LIGHT, highlightthickness=0)
        sb     = ttk.Scrollbar(self, orient="vertical",
                               command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)

        frame  = tk.Frame(canvas, bg=self.LIGHT)
        win_id = canvas.create_window((0, 0), window=frame, anchor="nw")

        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(win_id, width=e.width))
        frame.bind("<Configure>",
                   lambda e: canvas.configure(
                       scrollregion=canvas.bbox("all")))
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(
                            int(-1 * (e.delta / 120)), "units"))

        # ── Email card ────────────────────────────────────────────
        card = tk.Frame(frame, bg="#ffffff",
                        highlightbackground="#d0d0d0",
                        highlightthickness=1)
        card.pack(fill="x", padx=40, pady=24)

        # Header
        hdr = tk.Frame(card, bg=self.BLUE, pady=24)
        hdr.pack(fill="x")
        tk.Label(hdr, text="ACADEMIC REMINDER",
                 bg=self.BLUE, fg="#bee3f8",
                 font=("Segoe UI", 9, "bold")).pack()
        tk.Label(hdr, text="Exam Alert",
                 bg=self.BLUE, fg="#ffffff",
                 font=("Georgia", 22, "bold")).pack()

        # Urgency banner
        tk.Frame(card, bg=urgency_color, height=36).pack(fill="x")
        banner = tk.Frame(card, bg=urgency_color, pady=8)
        banner.pack(fill="x")
        tk.Label(banner,
                 text=f"Your exam is  {days_label.upper()}",
                 bg=urgency_color, fg="#ffffff",
                 font=("Segoe UI", 11, "bold")).pack()

        # Body
        body = tk.Frame(card, bg="#ffffff")
        body.pack(fill="x", padx=28, pady=20)

        tk.Label(body, text=f"Dear {name},",
                 bg="#ffffff", fg=self.TEXT,
                 font=("Segoe UI", 13, "bold"),
                 anchor="w").pack(fill="x", pady=(0, 8))

        tk.Label(body,
                 text="This is a friendly reminder that your upcoming exam\n"
                      "is just around the corner. Make sure you're prepared!",
                 bg="#ffffff", fg="#4a5568",
                 font=("Segoe UI", 10),
                 justify="left", anchor="w",
                 wraplength=520).pack(fill="x", pady=(0, 14))

        # Exam details box
        det = tk.Frame(body, bg="#ebf8ff",
                       highlightbackground="#bee3f8",
                       highlightthickness=2)
        det.pack(fill="x", pady=(0, 14))
        det_i = tk.Frame(det, bg="#ebf8ff")
        det_i.pack(fill="x", padx=16, pady=12)
        tk.Label(det_i, text="EXAM DETAILS",
                 bg="#ebf8ff", fg=self.LBLUE,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w",
                                                     pady=(0, 6))
        for label, value, color in [
            ("Course",    course,        self.TEXT),
            ("Date",      exam_date_str, self.TEXT),
            ("Time Left", days_label,    urgency_color),
        ]:
            r = tk.Frame(det_i, bg="#ebf8ff")
            r.pack(fill="x", pady=2)
            tk.Label(r, text=label,
                     bg="#ebf8ff", fg=self.GRAY,
                     font=("Segoe UI", 10),
                     width=10, anchor="w").pack(side="left")
            tk.Label(r, text=value,
                     bg="#ebf8ff", fg=color,
                     font=("Segoe UI", 10, "bold"),
                     anchor="w").pack(side="left")

        # Additional note
        if extra_note.strip():
            nf = tk.Frame(body, bg="#fffbeb",
                          highlightbackground="#f6ad55",
                          highlightthickness=2)
            nf.pack(fill="x", pady=(0, 14))
            ni = tk.Frame(nf, bg="#fffbeb")
            ni.pack(fill="x", padx=14, pady=10)
            tk.Label(ni, text="Additional Note",
                     bg="#fffbeb", fg="#92400e",
                     font=("Segoe UI", 9, "bold")).pack(anchor="w")
            tk.Label(ni, text=extra_note,
                     bg="#fffbeb", fg="#78350f",
                     font=("Segoe UI", 10),
                     justify="left", anchor="w",
                     wraplength=500).pack(anchor="w", pady=(4, 0))

        # Checklist
        tk.Label(body, text="Pre-Exam Checklist",
                 bg="#ffffff", fg=self.TEXT,
                 font=("Segoe UI", 10, "bold"),
                 anchor="w").pack(fill="x", pady=(0, 4))
        for item in [
            "Review all course materials and notes",
            "Confirm exam venue or online link",
            "Bring valid ID and permitted materials",
            "Get a good night's sleep",
        ]:
            tk.Label(body, text=f"  ✔  {item}",
                     bg="#ffffff", fg="#4a5568",
                     font=("Segoe UI", 10),
                     anchor="w").pack(fill="x", pady=1)

        tk.Label(body,
                 text="\nGood luck! Contact your instructor if needed.",
                 bg="#ffffff", fg=self.GRAY,
                 font=("Segoe UI", 9),
                 justify="left", anchor="w",
                 wraplength=520).pack(fill="x", pady=(10, 0))

        # PDF attachment list
        valid_pdfs = [p for p in (pdf_paths or [])
                      if p and os.path.exists(p)]
        if valid_pdfs:
            af = tk.Frame(card, bg="#f0fff4",
                          highlightbackground="#9ae6b4",
                          highlightthickness=1)
            af.pack(fill="x", padx=28, pady=(0, 16))
            ai = tk.Frame(af, bg="#f0fff4")
            ai.pack(fill="x", padx=14, pady=10)
            tk.Label(ai, text="Attachments",
                     bg="#f0fff4", fg="#276749",
                     font=("Segoe UI", 9, "bold")).pack(anchor="w")
            for p in valid_pdfs:
                tk.Label(ai,
                         text=f"  📄  {os.path.basename(p)}",
                         bg="#f0fff4", fg="#2f855a",
                         font=("Segoe UI", 10)).pack(anchor="w", pady=1)

        # Footer
        ftr = tk.Frame(card, bg="#f7fafc", pady=14)
        ftr.pack(fill="x")
        tk.Label(ftr,
                 text="Automated reminder — Academic Team",
                 bg="#f7fafc", fg="#a0aec0",
                 font=("Segoe UI", 8)).pack()
