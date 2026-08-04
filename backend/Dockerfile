# syntax=docker/dockerfile:1

# 3.11.x to match backend/runtime.txt (Render's separate buildpack deploy pins python-3.11.9);
# floating on the minor version rather than the exact patch keeps this pulling a maintained tag.

# ---- Builder: compiles/downloads dependencies only, discarded after this stage ----
FROM python:3.11-slim AS builder

WORKDIR /app

# build-essential covers any dependency without a prebuilt manylinux wheel; kept out of the
# final image entirely so it doesn't bloat the runtime layer.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ---- Runtime: only what's needed to actually run the app ----
FROM python:3.11-slim

# curl is only for the HEALTHCHECK below.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 appuser

WORKDIR /app

COPY --from=builder /root/.local /home/appuser/.local
COPY . .

# All settings fall back to safe defaults (see config/settings.py), so this needs no real
# secrets at build time. DEBUG is pinned off here as the container's baseline; the hosting
# platform's own env vars still override it (and everything else) at deploy time.
ENV DEBUG=False \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/home/appuser/.local/bin:$PATH

RUN python manage.py collectstatic --noinput \
    && chown -R appuser:appuser /app /home/appuser/.local

USER appuser

EXPOSE 10000

# No -f: a 404 (e.g. the bare "/" path, which this app doesn't route) still means gunicorn is
# up and answering requests, which is what this is actually checking for.
HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
    CMD curl -s -o /dev/null "http://127.0.0.1:${PORT:-10000}/" || exit 1

CMD gunicorn config.wsgi -c gunicorn.conf.py --bind 0.0.0.0:${PORT:-10000}
