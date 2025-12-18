from datetime import date, datetime, timedelta
import os
import tempfile

from szamlazz_collections_mcp import storage
from szamlazz_collections_mcp.config import reset_settings
from szamlazz_collections_mcp.models import InvoiceRecord


def test_insert_and_list_invoices(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        monkeypatch.setenv("DB_PATH", db_path)
        reset_settings()
        storage.init_db()
        record = InvoiceRecord(
            invoice_number="INV-1",
            buyer_name="Test Buyer",
            buyer_email="buyer@example.com",
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=7),
            gross_total=100.0,
            currency="HUF",
            status="open",
            created_at=datetime.utcnow(),
            last_reminded_at=None,
            reminders_sent_count=0,
            external_id=None,
        )
        storage.insert_invoice(record)
        invoices = storage.list_invoices()
        assert len(invoices) == 1
        assert invoices[0].invoice_number == "INV-1"
