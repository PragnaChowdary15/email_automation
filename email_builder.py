"""
email_builder.py
----------------
Builds personalized HTML emails with optional PDF attachments.
No SMTP logic here — just constructs the email object.
"""

import os
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders


def get_urgency(exam_date):
    """Return (days_label, urgency_color) based on days remaining."""
    days_left = (exam_date.date() - datetime.today().date()).days
    if days_left == 0:
        return "TODAY",    "#e53e3e"
    elif days_left == 1:
        return "TOMORROW", "#dd6b20"
    else:
        return f"in {days_left} days", "#2b6cb0"


def build_email_html(name, course, exam_date_str,
                     days_label, urgency_color, extra_note=""):
    """Return the HTML body string for the email."""

    note_block = ""
    if extra_note.strip():
        note_block = f"""
        <p style="font-size:14px;color:#2d3748;font-weight:600;margin:0 0 6px;">
          Additional Note:</p>
        <p style="font-size:14px;color:#4a5568;line-height:1.7;
                  background:#fffbeb;border-left:4px solid #f6ad55;
                  border-radius:6px;padding:10px 14px;margin:0 0 20px;">
          {extra_note}</p>"""

    return f"""<!DOCTYPE html><html><body style="margin:0;padding:0;
    background:#f4f6f9;font-family:'Segoe UI',Arial,sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0"
           style="background:#f4f6f9;padding:40px 0;"><tr><td align="center">
    <table width="600" cellpadding="0" cellspacing="0"
           style="background:#fff;border-radius:12px;
                  box-shadow:0 4px 20px rgba(0,0,0,.08);overflow:hidden;">
      <tr><td style="background:linear-gradient(135deg,#1a365d,#2b6cb0);
                     padding:36px 40px;text-align:center;">
        <p style="margin:0;color:#bee3f8;font-size:13px;
                  letter-spacing:3px;text-transform:uppercase;">Academic Reminder</p>
        <h1 style="margin:8px 0 0;color:#fff;font-size:28px;">Exam Alert</h1>
      </td></tr>
      <tr><td style="background:{urgency_color};padding:12px 40px;text-align:center;">
        <p style="margin:0;color:#fff;font-size:15px;font-weight:600;">
          Your exam is <strong>{days_label}</strong></p>
      </td></tr>
      <tr><td style="padding:40px;">
        <p style="font-size:17px;color:#2d3748;">
          Dear <strong>{name}</strong>,</p>
        <p style="font-size:15px;color:#4a5568;line-height:1.7;">
          This is a friendly reminder that your upcoming exam is
          just around the corner. Make sure you are fully prepared!</p>
        <table width="100%"
               style="background:#ebf8ff;border-left:4px solid #2b6cb0;
                      border-radius:8px;margin-bottom:24px;">
          <tr><td style="padding:20px 24px;">
            <p style="margin:0 0 10px;font-size:13px;color:#2b6cb0;
                      letter-spacing:2px;text-transform:uppercase;
                      font-weight:600;">Exam Details</p>
            <table cellpadding="6">
              <tr>
                <td style="font-size:14px;color:#718096;width:110px;">Course</td>
                <td style="font-size:15px;color:#1a202c;
                           font-weight:600;">{course}</td>
              </tr>
              <tr>
                <td style="font-size:14px;color:#718096;">Date</td>
                <td style="font-size:15px;color:#1a202c;
                           font-weight:600;">{exam_date_str}</td>
              </tr>
              <tr>
                <td style="font-size:14px;color:#718096;">Time Left</td>
                <td style="font-size:15px;color:{urgency_color};
                           font-weight:700;">{days_label}</td>
              </tr>
            </table>
          </td></tr>
        </table>
        {note_block}
        <p style="font-size:14px;color:#2d3748;font-weight:600;
                  margin:0 0 8px;">Pre-Exam Checklist</p>
        <table cellpadding="0" cellspacing="0" style="margin-bottom:24px;">
          <tr><td style="padding:4px 0;font-size:14px;color:#4a5568;">
            ✔  Review all course materials and notes</td></tr>
          <tr><td style="padding:4px 0;font-size:14px;color:#4a5568;">
            ✔  Confirm exam venue or online link</td></tr>
          <tr><td style="padding:4px 0;font-size:14px;color:#4a5568;">
            ✔  Bring valid ID and permitted materials</td></tr>
          <tr><td style="padding:4px 0;font-size:14px;color:#4a5568;">
            ✔  Get a good night's sleep</td></tr>
        </table>
        <p style="font-size:14px;color:#718096;line-height:1.7;">
          Good luck! Reach out to your instructor if you have questions.</p>
      </td></tr>
      <tr><td style="background:#f7fafc;padding:24px 40px;
                     border-top:1px solid #e2e8f0;text-align:center;">
        <p style="margin:0;font-size:12px;color:#a0aec0;">
          Automated reminder — Academic Team</p>
      </td></tr>
    </table></td></tr></table></body></html>"""


def build_mime_email(row, sender, pdf_paths=None, extra_note=""):
    """
    Build a complete MIME email for one student row.
    Attaches PDFs if provided.
    """
    name      = str(row["Name"]).strip()
    recipient = str(row["Email"]).strip()
    course    = str(row["Course"]).strip()
    exam_date = row["Exam_Date"].strftime("%B %d, %Y")

    days_label, urgency_color = get_urgency(row["Exam_Date"])
    subject = f"Exam Reminder: {course} is {days_label} — {exam_date}"

    html  = build_email_html(name, course, exam_date,
                             days_label, urgency_color, extra_note)
    plain = (f"Dear {name},\n\nReminder: {course} exam on {exam_date} "
             f"({days_label}).\n\nGood luck!\nThe Academic Team")

    msg = MIMEMultipart("mixed")
    msg["Subject"] = subject
    msg["From"]    = sender
    msg["To"]      = recipient

    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText(plain, "plain"))
    alt.attach(MIMEText(html,  "html"))
    msg.attach(alt)

    # Attach PDFs
    for pdf_path in (pdf_paths or []):
        if not pdf_path or not os.path.exists(pdf_path):
            continue
        with open(pdf_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition",
                        f'attachment; filename="{os.path.basename(pdf_path)}"')
        msg.attach(part)

    return msg
