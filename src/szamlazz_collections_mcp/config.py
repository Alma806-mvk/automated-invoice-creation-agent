from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    mcp_token: str = os.getenv("MCP_TOKEN", "change-me")
    mcp_transport: str = os.getenv("MCP_TRANSPORT", "http")
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    mcp_path: str = os.getenv("MCP_PATH", "/mcp")

    szamlazz_agent_key: Optional[str] = os.getenv("SZAMLAZZ_AGENT_KEY")
    szamlazz_username: Optional[str] = os.getenv("SZAMLAZZ_USERNAME")
    szamlazz_password: Optional[str] = os.getenv("SZAMLAZZ_PASSWORD")

    db_path: str = os.getenv("DB_PATH", "./data/app.db")

    smtp_host: Optional[str] = os.getenv("SMTP_HOST")
    smtp_port: Optional[int] = int(os.getenv("SMTP_PORT", "587")) if os.getenv("SMTP_PORT") else None
    smtp_user: Optional[str] = os.getenv("SMTP_USER")
    smtp_password: Optional[str] = os.getenv("SMTP_PASSWORD")
    smtp_from: Optional[str] = os.getenv("SMTP_FROM")

    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    @property
    def has_smtp(self) -> bool:
        return bool(self.smtp_host and self.smtp_port and self.smtp_user and self.smtp_password and self.smtp_from)

    @property
    def has_agent_key(self) -> bool:
        return bool(self.szamlazz_agent_key)


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    global _settings
    _settings = None


def configure_logging(level: Optional[str] = None) -> None:
    log_level = level or get_settings().log_level
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
