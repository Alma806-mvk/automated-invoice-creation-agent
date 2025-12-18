from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Optional

from fastmcp import FastMCP, MCP
from fastmcp.annotations import ToolAnnotation
from fastmcp.auth import StaticTokenVerifier
from fastmcp.context import Context

from .config import configure_logging, get_settings
from .emailer import render_reminder, send_email
from .models import InvoiceCreate, InvoiceRecord
from .storage import (
    aging_summary,
    get_invoice,
    init_db,
    insert_invoice,
    list_invoices,
    list_overdue,
    mark_invoice_paid,
    update_reminder_metadata,
)
from .szamlazz_client import generate_invoice, query_invoice_pdf, query_invoice_xml, register_payment

configure_logging()
logger = logging.getLogger(__name__)
settings = get_settings()

app: MCP = FastMCP("szamlazz-collections", description="Számlázz.hu collections MCP server")
verifier = StaticTokenVerifier(token=settings.mcp_token)
app.set_auth(verifier)


@app.tool(
    title="Health check",
    annotations=[ToolAnnotation(readOnlyHint=True)],
)
def health_check() -> dict:
    return {"status": "ok", "version": "0.1.0"}


@app.tool(
    title="Create invoice",
    annotations=[ToolAnnotation(readOnlyHint=False, destructiveHint=False, openWorldHint=True)],
)
def create_invoice(invoice: InvoiceCreate, context: Optional[Context] = None) -> dict:
    payload = invoice.model_dump()
    result = generate_invoice(payload)
    invoice_number = result.get("invoice_number") or "unknown"
    record = InvoiceRecord(
        invoice_number=invoice_number,
        buyer_name=invoice.buyer.name,
        buyer_email=invoice.buyer.email,
        issue_date=invoice.issue_date,
        due_date=invoice.due_date,
        gross_total=sum(item.gross_value for item in invoice.items),
        currency=invoice.currency,
        status="open",
        created_at=datetime.utcnow(),
        last_reminded_at=None,
        reminders_sent_count=0,
        external_id=invoice.external_id,
    )
    insert_invoice(record)
    return {
        "invoice_number": invoice_number,
        "stored_record": record.model_dump(),
        "raw_response_summary": result.get("raw_response_summary"),
    }


@app.tool(
    title="Query invoice PDF",
    annotations=[ToolAnnotation(readOnlyHint=True)],
)
def query_invoice_pdf_tool(invoice_number: str, save: bool = True) -> dict:
    return query_invoice_pdf(invoice_number, save=save)


@app.tool(
    title="Query invoice XML",
    annotations=[ToolAnnotation(readOnlyHint=True)],
)
def query_invoice_xml_tool(invoice_number: str) -> dict:
    return query_invoice_xml(invoice_number)


@app.tool(
    title="List invoices",
    annotations=[ToolAnnotation(readOnlyHint=True)],
)
def list_invoices_tool(
    status: Optional[str] = None, due_before: Optional[date] = None, customer_email: Optional[str] = None
) -> list[InvoiceRecord]:
    return list_invoices(status=status, due_before=due_before, customer_email=customer_email)


@app.tool(
    title="List overdue invoices",
    annotations=[ToolAnnotation(readOnlyHint=True)],
)
def list_overdue_invoices(min_days_overdue: int = 1) -> list[InvoiceRecord]:
    return list_overdue(min_days_overdue)


@app.tool(
    title="Mark invoice paid (local)",
    annotations=[ToolAnnotation(readOnlyHint=False, destructiveHint=False, openWorldHint=False)],
)
def mark_invoice_paid_local(invoice_number: str, paid_date: date) -> dict:
    record = mark_invoice_paid(invoice_number, paid_date)
    if not record:
        return {"invoice_number": invoice_number, "status": "not_found"}
    return {"invoice_number": invoice_number, "status": record.status}


@app.tool(
    title="Register payment in Számlázz.hu",
    annotations=[ToolAnnotation(readOnlyHint=False, destructiveHint=False, openWorldHint=True)],
)
def register_payment_in_szamlazz(invoice_number: str, paid_date: date, amount: float, currency: str = "HUF") -> dict:
    response = register_payment(invoice_number, paid_date.isoformat(), amount, currency)
    return response


@app.tool(
    title="Generate reminder email",
    annotations=[ToolAnnotation(readOnlyHint=True)],
)
def generate_reminder_email(invoice_number: str, language: str = "hu", tone: str = "polite") -> dict:
    record = get_invoice(invoice_number)
    if not record:
        raise ValueError("Invoice not found in local store")
    draft = render_reminder(record, language=language, tone=tone)
    return draft.model_dump()


@app.tool(
    title="Send reminder via SMTP",
    annotations=[ToolAnnotation(readOnlyHint=False, destructiveHint=False, openWorldHint=True)],
)
def send_reminder_email_smtp(
    invoice_number: str, to_email: Optional[str] = None, language: str = "hu", tone: str = "polite"
) -> dict:
    record = get_invoice(invoice_number)
    if not record:
        raise ValueError("Invoice not found in local store")
    target_email = to_email or record.buyer_email
    draft = render_reminder(record, language=language, tone=tone)
    result = send_email(target_email, draft)
    update_reminder_metadata(invoice_number)
    return result


@app.tool(
    title="Aging summary",
    annotations=[ToolAnnotation(readOnlyHint=True)],
)
def aging_summary_tool() -> dict:
    return aging_summary()


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    logger.info("MCP server started")


def run() -> None:
    transport = settings.mcp_transport or "http"
    app.run(transport=transport, host=settings.host, port=settings.port, path=settings.mcp_path)


if __name__ == "__main__":
    run()
