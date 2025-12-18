from __future__ import annotations

import logging
import mimetypes
import os
import re
from typing import Any, Dict, Optional

import httpx
from jinja2 import Environment, FileSystemLoader, select_autoescape

from .config import get_settings
from .utils import encode_pdf, summarize_response

logger = logging.getLogger(__name__)

BASE_URL = "https://www.szamlazz.hu/szamla/"


def _jinja_env() -> Environment:
    templates_path = os.path.join(os.path.dirname(__file__), "xml_templates")
    return Environment(
        loader=FileSystemLoader(templates_path),
        autoescape=select_autoescape(enabled_extensions=(".xml",)),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def build_xml(template_name: str, data: Dict[str, Any]) -> str:
    env = _jinja_env()
    template = env.get_template(template_name)
    return template.render(**data)


def _auth_fragment() -> Dict[str, Any]:
    settings = get_settings()
    if settings.szamlazz_agent_key:
        return {"agent_key": settings.szamlazz_agent_key}
    return {
        "username": settings.szamlazz_username,
        "password": settings.szamlazz_password,
    }


def post_xml(field_name: str, xml_str: str) -> httpx.Response:
    files = {field_name: ("request.xml", xml_str.encode("utf-8"), "text/xml")}
    logger.debug("Posting to Szamlazz.hu field=%s", field_name)
    client = httpx.Client()
    response = client.post(BASE_URL, files=files, timeout=30.0)
    response.raise_for_status()
    return response


def _parse_invoice_number(text: str) -> Optional[str]:
    match = re.search(r"DONE;\s*([A-Za-z0-9\-\/]+)", text)
    if match:
        return match.group(1)
    match = re.search(r"<invoiceNumber>(.*?)</invoiceNumber>", text, re.IGNORECASE)
    if match:
        return match.group(1)
    return None


def generate_invoice(payload: Dict[str, Any]) -> Dict[str, Any]:
    data = {**payload, **_auth_fragment()}
    xml = build_xml("generate_invoice.xml.j2", data)
    response = post_xml("action-xmlagentxmlfile", xml)
    content_type = response.headers.get("content-type", "")
    invoice_number = None
    raw_summary = ""
    pdf_b64 = None

    if response.content.startswith(b"%PDF") or "pdf" in content_type:
        pdf_b64 = encode_pdf(response.content)
    else:
        raw_text = response.text
        raw_summary = summarize_response(raw_text)
        invoice_number = _parse_invoice_number(raw_text)

    return {
        "invoice_number": invoice_number,
        "pdf_base64": pdf_b64,
        "raw_response_summary": raw_summary,
    }


def query_invoice_pdf(invoice_number: str, save: bool = True, output_dir: str = "./data") -> Dict[str, Any]:
    data = {"invoice_number": invoice_number, **_auth_fragment()}
    xml = build_xml("query_invoice_pdf.xml.j2", data)
    response = post_xml("action-szamla_agent_pdf", xml)
    if not response.content.startswith(b"%PDF"):
        raise ValueError("Unexpected response when fetching PDF")

    file_path = None
    pdf_b64 = encode_pdf(response.content)
    if save:
        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, f"{invoice_number}.pdf")
        with open(file_path, "wb") as f:
            f.write(response.content)
    return {"invoice_number": invoice_number, "pdf_base64": pdf_b64, "file_path": file_path}


def query_invoice_xml(invoice_number: str) -> Dict[str, Any]:
    data = {"invoice_number": invoice_number, **_auth_fragment()}
    xml = build_xml("query_invoice_xml.xml.j2", data)
    response = post_xml("action-szamla_agent_xml", xml)
    return {"invoice_number": invoice_number, "xml": response.text}


def register_payment(invoice_number: str, paid_date: str, amount: float, currency: str = "HUF") -> Dict[str, Any]:
    data = {
        "invoice_number": invoice_number,
        "paid_date": paid_date,
        "amount": amount,
        "currency": currency,
        **_auth_fragment(),
    }
    xml = build_xml("register_payment.xml.j2", data)
    response = post_xml("action-szamla_agent_kifiz", xml)
    summary = summarize_response(response.text)
    ok = "DONE" in response.text.upper()
    return {"ok": ok, "message": summary}
