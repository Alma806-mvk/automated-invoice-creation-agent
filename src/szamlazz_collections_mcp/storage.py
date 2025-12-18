from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import List, Optional

from .models import InvoiceRecord
from .utils import db_connection

logger = logging.getLogger(__name__)


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS invoices (
    invoice_number TEXT PRIMARY KEY,
    buyer_name TEXT NOT NULL,
    buyer_email TEXT NOT NULL,
    issue_date DATE NOT NULL,
    due_date DATE NOT NULL,
    gross_total REAL NOT NULL,
    currency TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    last_reminded_at TIMESTAMP,
    reminders_sent_count INTEGER NOT NULL DEFAULT 0,
    external_id TEXT
);
"""


def init_db() -> None:
    with db_connection() as conn:
        conn.execute(CREATE_TABLE_SQL)
        conn.commit()
        logger.debug("Database initialized")


def insert_invoice(record: InvoiceRecord) -> None:
    with db_connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO invoices (
                invoice_number, buyer_name, buyer_email, issue_date, due_date,
                gross_total, currency, status, created_at, last_reminded_at,
                reminders_sent_count, external_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.invoice_number,
                record.buyer_name,
                record.buyer_email,
                record.issue_date,
                record.due_date,
                record.gross_total,
                record.currency,
                record.status,
                record.created_at,
                record.last_reminded_at,
                record.reminders_sent_count,
                record.external_id,
            ),
        )
        conn.commit()
        logger.info("Stored invoice %s", record.invoice_number)


def update_reminder_metadata(invoice_number: str) -> None:
    with db_connection() as conn:
        conn.execute(
            """
            UPDATE invoices
            SET reminders_sent_count = reminders_sent_count + 1,
                last_reminded_at = ?
            WHERE invoice_number = ?
            """,
            (datetime.utcnow(), invoice_number),
        )
        conn.commit()


def mark_invoice_paid(invoice_number: str, paid_date: date) -> Optional[InvoiceRecord]:
    with db_connection() as conn:
        conn.execute(
            """
            UPDATE invoices
            SET status = 'paid', last_reminded_at = ?, reminders_sent_count = reminders_sent_count
            WHERE invoice_number = ?
            """,
            (datetime.combine(paid_date, datetime.min.time()), invoice_number),
        )
        conn.commit()
    return get_invoice(invoice_number)


def get_invoice(invoice_number: str) -> Optional[InvoiceRecord]:
    with db_connection() as conn:
        cur = conn.execute("SELECT * FROM invoices WHERE invoice_number = ?", (invoice_number,))
        row = cur.fetchone()
        if not row:
            return None
        return InvoiceRecord(**dict(row))


def list_invoices(
    status: Optional[str] = None, due_before: Optional[date] = None, customer_email: Optional[str] = None
) -> List[InvoiceRecord]:
    query = "SELECT * FROM invoices WHERE 1=1"
    params = []
    if status:
        query += " AND status = ?"
        params.append(status)
    if due_before:
        query += " AND due_date <= ?"
        params.append(due_before)
    if customer_email:
        query += " AND buyer_email = ?"
        params.append(customer_email)

    query += " ORDER BY due_date ASC"

    with db_connection() as conn:
        cur = conn.execute(query, params)
        rows = cur.fetchall()
        return [InvoiceRecord(**dict(row)) for row in rows]


def list_overdue(min_days_overdue: int = 1) -> List[InvoiceRecord]:
    cutoff = date.today() - timedelta(days=min_days_overdue)
    query = "SELECT * FROM invoices WHERE status = 'open' AND due_date < ? ORDER BY due_date ASC"
    with db_connection() as conn:
        cur = conn.execute(query, (cutoff,))
        rows = cur.fetchall()
        return [InvoiceRecord(**dict(row)) for row in rows]


def aging_summary() -> dict:
    buckets = {
        "current": (0, 0),
        "1-7": (1, 7),
        "8-30": (8, 30),
        "31-60": (31, 60),
        "60+": (61, 9999),
    }
    results = {key: {"count": 0, "gross_total": 0.0} for key in buckets}
    totals = {"count": 0, "gross_total": 0.0}

    with db_connection() as conn:
        cur = conn.execute("SELECT status, due_date, gross_total FROM invoices")
        for status, due_date, gross_total in cur.fetchall():
            totals["count"] += 1
            totals["gross_total"] += gross_total
            if status != "open":
                continue
            days_overdue = (date.today() - due_date).days
            if days_overdue <= 0:
                bucket = "current"
            elif days_overdue <= 7:
                bucket = "1-7"
            elif days_overdue <= 30:
                bucket = "8-30"
            elif days_overdue <= 60:
                bucket = "31-60"
            else:
                bucket = "60+"
            results[bucket]["count"] += 1
            results[bucket]["gross_total"] += gross_total

    return {"by_bucket": results, "totals": totals}
