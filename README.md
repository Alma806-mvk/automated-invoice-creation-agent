# Számlázz.hu Collections MCP Server

Turnkey FastMCP server that lets ChatGPT create invoices, track collections, and send polite reminders via Számlázz.hu.

## Features
- Create invoices via Számlázz.hu Agent API (XML multipart)
- Store invoice metadata locally in SQLite
- Query invoice PDF/XML, register payments
- Overdue listing and aging summary reporting
- Generate bilingual reminder emails and optionally send via SMTP
- Secured with static bearer token for MCP HTTP transport

## Quick start
1. **Install uv** (or use any PEP 517 frontend):
   ```bash
   pip install uv
   ```
2. **Sync dependencies**:
   ```bash
   uv sync
   ```
3. **Create environment file**:
   ```bash
   cp .env.example .env
   # fill MCP_TOKEN, SZAMLAZZ_AGENT_KEY, SMTP_*
   ```
4. **Run the server locally**:
   ```bash
   uv run fastmcp run src/szamlazz_collections_mcp/server.py
   ```
   The server defaults to HTTP transport on `0.0.0.0:8000` at `/mcp`.

## Environment variables
See `.env.example` for the full list. Key values:
- `MCP_TOKEN`: bearer token required for MCP requests.
- `MCP_TRANSPORT`: `http` (default) or `sse`.
- `HOST` / `PORT` / `MCP_PATH`: network configuration for the MCP HTTP endpoint.
- `SZAMLAZZ_AGENT_KEY` or `SZAMLAZZ_USERNAME`+`SZAMLAZZ_PASSWORD`: authentication to Számlázz.hu.
- `DB_PATH`: SQLite path (default `./data/app.db`).
- `SMTP_*`: SMTP host/port/user/password/from for sending reminder emails.

## Running with Docker
```
docker build -t szamlazz-collections .
docker run -p 8000:8000 --env-file .env szamlazz-collections
```

## Docker Compose
```
docker-compose up --build
```

## Deployment notes
- The server binds to `0.0.0.0` and reads `PORT` for PaaS compatibility.
- Replace `StaticTokenVerifier` with OAuth in `server.py` when moving to production.
- Keep secrets out of git; use environment variables or platform secret stores.

## Connecting from ChatGPT (Business developer mode)
Use the MCP remote endpoint URL (e.g., `https://your-domain/mcp`) and configure the same `MCP_TOKEN` as a bearer credential.

## Tests and linting
```
uv run pytest
uv run ruff check .
```

## License
MIT
