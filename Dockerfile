# selfhost-remote-mail-mcp as a web server (serve mode). Works on amd64 and arm64.
FROM python:3.14-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.11.19 /uv /bin/uv

WORKDIR /app

# dependencies first, so code changes rebuild fast
COPY pyproject.toml uv.lock README.md LICENSE NOTICE CHANGELOG.md ./
RUN uv sync --frozen --no-install-project --no-dev

COPY src ./src
RUN uv sync --frozen --no-dev

# Everything that must survive a restart (login tokens, send log, signature, templates) lives in /data.
# Mount a persistent volume or disk there. Without one it still works, but after each restart
# you log in again and the send limits start from zero.
ENV HOST=0.0.0.0 \
    PORT=8765 \
    MAIL_CONFIG_DIR=/data \
    DATA_DIR=/data \
    PATH="/app/.venv/bin:$PATH"
EXPOSE 8765

HEALTHCHECK --interval=60s --timeout=5s CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\", \"8765\")}/health')"

CMD ["selfhost-remote-mail-mcp", "serve"]
