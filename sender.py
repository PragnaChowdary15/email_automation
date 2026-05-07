"""
sender.py
---------
Handles all SMTP sending logic and CSV logging.
Completely separate from the GUI — can be used standalone too.
"""

import smtplib
import csv
import time
import os
import pandas as pd
from datetime import datetime, timedelta

from utils import parse_dates
from email_builder import build_mime_email


def run_email_job(csv_path, sender_email, sender_password,
                  smtp_server, smtp_port, days_ahead,
                  log_path, pdf_paths, extra_note,
                  log_callback):
    """
    Main email job:
      1. Load & validate CSV
      2. Filter by exam date
      3. Connect to SMTP
      4. Send personalized email to each student
      5. Log every result to CSV
    
    log_callback(msg) is called for every status update
    so the GUI or terminal can display it.
    Returns True if at least one email was sent, False otherwise.
    """

    def log(msg):
        log_callback(msg)

    # ── 1. Load CSV ────────────────────────────────────────────────
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        log(f"[ERROR] CSV not found: '{csv_path}'")
        return False
    except Exception as e:
        log(f"[ERROR] Cannot read CSV: {e}")
        return False

    required = {"Name", "Email", "Course", "Exam_Date"}
    missing  = required - set(df.columns)
    if missing:
        log(f"[ERROR] Missing columns: {missing}")
        log("        Required: Name, Email, Course, Exam_Date")
        return False

    df = df.dropna(subset=["Email"])

    # ── 2. Parse & filter dates ────────────────────────────────────
    try:
        df["Exam_Date"] = parse_dates(df["Exam_Date"])
        log("[INFO] Dates parsed OK.")
    except Exception as e:
        log(f"[ERROR] {e}")
        return False

    today  = datetime.today().date()
    target = today + timedelta(days=days_ahead)
    mask   = ((df["Exam_Date"].dt.date >= today) &
               (df["Exam_Date"].dt.date <= target))
    df     = df[mask].copy()

    log(f"[INFO] Found {len(df)} student(s) with exam "
        f"in the next {days_ahead} day(s).\n")

    if df.empty:
        log(f"[INFO] No exams between {today} and {target}.")
        log("[TIP]  Update your CSV dates or increase Days Ahead.")
        return False

    if pdf_paths:
        valid_pdfs = [p for p in pdf_paths if p and os.path.exists(p)]
        if valid_pdfs:
            log(f"[INFO] Attaching {len(valid_pdfs)} PDF file(s).")

    # ── 3. Init log file ───────────────────────────────────────────
    log_exists = os.path.exists(log_path)
    log_file   = open(log_path, "a", newline="")
    writer     = csv.writer(log_file)
    if not log_exists:
        writer.writerow(["Timestamp", "Name", "Email",
                         "Course", "Exam_Date", "Status", "Note"])

    success = failed = skipped = 0

    # ── 4. Connect & send ──────────────────────────────────────────
    try:
        log("[INFO] Connecting to SMTP server ...")
        with smtplib.SMTP(smtp_server, int(smtp_port)) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(sender_email, sender_password)
            log("[INFO] Login successful!\n")

            for _, row in df.iterrows():
                recipient = str(row["Email"]).strip()
                name      = str(row["Name"]).strip()
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # Basic format check
                if ("@" not in recipient or
                        "." not in recipient.split("@")[-1]):
                    log(f"  [SKIP]  {name} | '{recipient}' — invalid format")
                    writer.writerow([timestamp, name, recipient,
                                     row["Course"],
                                     row["Exam_Date"].strftime("%Y-%m-%d"),
                                     "SKIPPED", "Invalid email format"])
                    skipped += 1
                    continue

                try:
                    msg = build_mime_email(row, sender_email,
                                          pdf_paths, extra_note)
                    server.sendmail(sender_email, recipient, msg.as_string())
                    log(f"  [OK]  {name}  |  {recipient}")
                    writer.writerow([timestamp, name, recipient,
                                     row["Course"],
                                     row["Exam_Date"].strftime("%Y-%m-%d"),
                                     "SUCCESS", ""])
                    success += 1

                except Exception as e:
                    log(f"  [FAIL]  {name}  |  {recipient}  —  {e}")
                    writer.writerow([timestamp, name, recipient,
                                     row["Course"],
                                     row["Exam_Date"].strftime("%Y-%m-%d"),
                                     "FAILED", str(e)])
                    failed += 1

                time.sleep(1)   # avoid Gmail rate limits

    except smtplib.SMTPAuthenticationError:
        log("\n[ERROR] Login failed — wrong email or App Password.")
        log("[TIP]   Use a Gmail App Password (16 chars).")
        log_file.close()
        return False

    except smtplib.SMTPConnectError:
        log(f"\n[ERROR] Cannot connect to {smtp_server}:{smtp_port}.")
        log_file.close()
        return False

    except Exception as e:
        log(f"\n[ERROR] {e}")
        log_file.close()
        return False

    # ── 5. Summary ─────────────────────────────────────────────────
    log_file.close()
    log("\n" + "=" * 50)
    log(f"  DONE  |  Sent: {success}  |  "
        f"Failed: {failed}  |  Skipped: {skipped}")
    log(f"  Log saved to: {log_path}")
    log("=" * 50)
    return True
