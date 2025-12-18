from __future__ import annotations

import base64
import os
import sqlite3
from contextlib import contextmanager
from typing import Generator, Optional

from .config import get_settings


def ensure_data_dir() -> None:
    db_path = get_settings().db_path
    directory = os.path.dirname(db_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)


@contextmanager
def db_connection() -> Generator[sqlite3.Connection, None, None]:
    ensure_data_dir()
    conn = sqlite3.connect(get_settings().db_path, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def encode_pdf(pdf_bytes: bytes) -> str:
    return base64.b64encode(pdf_bytes).decode()


def summarize_response(response_text: str, limit: int = 300) -> str:
    sanitized = response_text.strip().replace("\n", " ")
    return sanitized[:limit]
