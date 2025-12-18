from datetime import date, datetime, timedelta
import os
import tempfile

from szamlazz_collections_mcp import storage
from szamlazz_collections_mcp.config import reset_settings
from szamlazz_collections_mcp.models import InvoiceRecord


def test_overdue_listing(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        monkeypatch.setenv("DB_PATH", db_path)
        reset_settings()
        storage.init_db()
        today = date.today()
        overdue_record = InvoiceRecord(
            invoice_number="INV-OD",
            buyer_name="Late Buyer",
            buyer_email="late@example.com",
            issue_date=today - timedelta(days=10),
            due_date=today - timedelta(days=5),
            gross_total=50.0,
            currency="HUF",
            status="open",
            created_at=datetime.utcnow(),
            last_reminded_at=None,
            reminders_sent_count=0,
            external_id=None,
        )
        storage.insert_invoice(overdue_record)
        overdue = storage.list_overdue()
        assert len(overdue) == 1
        assert overdue[0].invoice_number == "INV-OD"


def test_aging_summary(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        monkeypatch.setenv("DB_PATH", db_path)
        reset_settings()
        storage.init_db()
        today = date.today()
        record_current = InvoiceRecord(
            invoice_number="INV-CUR",
            buyer_name="Current",
            buyer_email="c@example.com",
            issue_date=today,
            due_date=today + timedelta(days=2),
            gross_total=100.0,
            currency="HUF",
            status="open",
            created_at=datetime.utcnow(),
            last_reminded_at=None,
            reminders_sent_count=0,
            external_id=None,
        )
        record_overdue = InvoiceRecord(
            invoice_number="INV-OVER",
            buyer_name="Old",
            buyer_email="o@example.com",
            issue_date=today - timedelta(days=40),
            due_date=today - timedelta(days=35),
            gross_total=200.0,
            currency="HUF",
            status="open",
            created_at=datetime.utcnow(),
            last_reminded_at=None,
            reminders_sent_count=0,
            external_id=None,
        )
        storage.insert_invoice(record_current)
        storage.insert_invoice(record_overdue)
        summary = storage.aging_summary()
        assert summary["totals"]["count"] == 2
        assert summary["by_bucket"]["31-60"]["count"] == 1
