from __future__ import annotations

import logging
import os
import smtplib
from datetime import date
from email.message import EmailMessage
from typing import Optional

from jinja2 import Environment, FileSystemLoader

from .config import get_settings
from .models import InvoiceRecord, ReminderDraft

logger = logging.getLogger(__name__)


def _jinja_env() -> Environment:
    templates_path = os.path.join(os.path.dirname(__file__), "templates")
    return Environment(loader=FileSystemLoader(templates_path), autoescape=False)


def render_reminder(record: InvoiceRecord, language: str = "hu", tone: str = "polite") -> ReminderDraft:
    env = _jinja_env()
    template_name = f"reminder_{language}.txt.j2"
    template = env.get_template(template_name)
    body = template.render(
        buyer_name=record.buyer_name,
        invoice_number=record.invoice_number,
        due_date=record.due_date,
        amount=record.gross_total,
        tone=tone,
    )
    subject = {
        "hu": f"Kíméletes emlékeztető: Számla {record.invoice_number}",
        "en": f"Friendly reminder: Invoice {record.invoice_number}",
    }.get(language, f"Invoice {record.invoice_number} reminder")

    return ReminderDraft(
        subject=subject,
        body=body,
        language=language,
        tone=tone,
        invoice_number=record.invoice_number,
        amount=record.gross_total,
        due_date=record.due_date,
    )


def send_email(to_email: str, draft: ReminderDraft) -> dict:
    settings = get_settings()
    if not settings.has_smtp:
        raise RuntimeError("SMTP is not configured. Set SMTP_* environment variables.")

    msg = EmailMessage()
    msg["Subject"] = draft.subject
    msg["From"] = settings.smtp_from
    msg["To"] = to_email
    msg.set_content(draft.body)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(msg)
    logger.info("Sent reminder to %s", to_email)
    return {"ok": True, "sent_to": to_email, "message": "Email sent"}
