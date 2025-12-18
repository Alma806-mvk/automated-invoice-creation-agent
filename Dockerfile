FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir uv && uv sync
COPY src ./src
COPY README.md .

ENV HOST=0.0.0.0
ENV PORT=8000
ENV MCP_PATH=/mcp

CMD ["uv", "run", "fastmcp", "run", "src/szamlazz_collections_mcp/server.py"]
