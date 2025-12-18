from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field, validator


class Buyer(BaseModel):
    name: str
    country: str = Field(default="HU", description="ISO country code")
    zip: str
    city: str
    address: str
    email: str
    tax_number: Optional[str] = None
    identifier: Optional[str] = Field(default=None, description="External customer identifier")


class Item(BaseModel):
    name: str
    quantity: float
    net_unit_price: float
    vat_rate: float
    net_value: float
    vat_value: float
    gross_value: float
    comment: Optional[str] = None

    @validator("net_value", "vat_value", "gross_value")
    def non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Amounts must be non-negative")
        return v


class InvoiceCreate(BaseModel):
    buyer: Buyer
    items: List[Item]
    payment_method: str
    currency: str = "HUF"
    issue_date: date
    due_date: date
    invoice_language: str = "hu"
    comment: Optional[str] = None
    order_number: Optional[str] = None
    external_id: Optional[str] = None


class InvoiceRecord(BaseModel):
    invoice_number: str
    buyer_name: str
    buyer_email: str
    issue_date: date
    due_date: date
    gross_total: float
    currency: str
    status: str
    created_at: datetime
    last_reminded_at: Optional[datetime]
    reminders_sent_count: int
    external_id: Optional[str] = None


class ReminderDraft(BaseModel):
    subject: str
    body: str
    language: str
    tone: str
    invoice_number: str
    amount: float
    due_date: date
