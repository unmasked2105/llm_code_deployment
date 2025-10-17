import json
import os
import smtplib
from email.message import EmailMessage
from typing import Dict
import requests


def notify_evaluator(url: str, payload: Dict) -> None:

    eval_format = os.getenv("EVAL_FORMAT", "json").lower()
    if eval_format == "formspree":
        # Formspree expects typical form fields; JSON is accepted with appropriate headers.
        body = {
            "subject": f"Generation completed: {payload.get('project_name', '')}",
            "project_name": payload.get("project_name", ""),
            "repo_url": payload.get("repo_url", ""),
            "metadata": json.dumps(payload.get("metadata", {})),
        }
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        requests.post(url, data=json.dumps(body), headers=headers, timeout=20)
        return

    headers = {"Content-Type": "application/json"}
    requests.post(url, data=json.dumps(payload), headers=headers, timeout=20)


def send_email_notification(subject: str, body: str) -> None:

    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    mail_from = os.getenv("MAIL_FROM")
    mail_to = os.getenv("MAIL_TO")

    if not (smtp_host and smtp_user and smtp_pass and mail_from and mail_to):
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = mail_from
    msg["To"] = mail_to
    msg.set_content(body)

    with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)


