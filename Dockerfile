# syntax=docker/dockerfile:1.7
#
# MiroFish — production multi-stage image
# -----------------------------------------------------------------------------
# Stage 1 "frontend-build": builds the Vue app with Vite and produces
#   /build/frontend/dist (static assets).
# Stage 2 "backend-deps":   resolves the Python virtualenv via uv.
# Stage 3 "runtime":        slim Python base that copies in only what's needed
#   to run. The frontend is served by vite preview (same port 3000 as dev);
#   the backend runs via gunicorn for a production WSGI server.
#
# The previous single-stage development image is kept as `Dockerfile.dev` for
# users who want hot-reload inside a container.

############################  Stage 1: frontend  #############################
FROM node:20-bookworm-slim AS frontend-build

WORKDIR /build/frontend

# Install deps first for layer caching.
COPY frontend/package.json frontend/package-lock.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci --no-audit --no-fund

COPY frontend/ ./
# Produces /build/frontend/dist
RUN npm run build


############################  Stage 2: backend deps  #########################
FROM python:3.11-slim-bookworm AS backend-deps

# uv for fast, reproducible Python dependency resolution
COPY --from=ghcr.io/astral-sh/uv:0.9.26 /uv /uvx /bin/

WORKDIR /build/backend
COPY backend/pyproject.toml backend/uv.lock ./
# --frozen uses the lockfile exactly; --no-dev skips dev-only deps
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev


############################  Stage 3: runtime  ##############################
FROM python:3.11-slim-bookworm AS runtime

# Only install Node here to run `vite preview` for the static frontend server
# (keeps image size far smaller than the full Node dev image).
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        nodejs \
        npm \
        tini \
    && rm -rf /var/lib/apt/lists/*

# Non-root user for defence in depth
RUN useradd --create-home --shell /bin/bash mirofish

WORKDIR /app

# Copy resolved Python venv from the backend-deps stage
COPY --from=backend-deps /build/backend/.venv /app/backend/.venv
ENV PATH="/app/backend/.venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install gunicorn for a production WSGI server (separate from app deps so
# users who vendor their own WSGI server can swap it out easily).
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir "gunicorn>=22.0.0"

# Copy application code
COPY --chown=mirofish:mirofish backend/ /app/backend/
COPY --chown=mirofish:mirofish locales/ /app/locales/
COPY --chown=mirofish:mirofish static/ /app/static/
COPY --chown=mirofish:mirofish package.json package-lock.json /app/
COPY --chown=mirofish:mirofish frontend/package.json frontend/package-lock.json frontend/vite.config.js /app/frontend/

# Copy the pre-built frontend bundle
COPY --from=frontend-build --chown=mirofish:mirofish /build/frontend/dist /app/frontend/dist

# Install a minimal runtime node_modules — just enough for `vite preview`.
WORKDIR /app/frontend
RUN --mount=type=cache,target=/root/.npm \
    npm install --omit=dev --no-audit --no-fund vite \
    && chown -R mirofish:mirofish /app/frontend

WORKDIR /app

# Launcher: starts backend and frontend preview, exits if either dies
COPY --chown=mirofish:mirofish <<'EOF' /app/entrypoint.sh
#!/bin/sh
# Fail fast on any process exit so container orchestrators can restart cleanly.
set -e

cd /app/backend
# FLASK_HOST defaults to 0.0.0.0 for container networking; gunicorn workers
# and threads are modest defaults suitable for a single small instance.
exec_backend() {
    cd /app/backend
    exec gunicorn \
        --bind "0.0.0.0:${FLASK_PORT:-5001}" \
        --workers "${GUNICORN_WORKERS:-2}" \
        --threads "${GUNICORN_THREADS:-4}" \
        --timeout "${GUNICORN_TIMEOUT:-120}" \
        --access-logfile - \
        --error-logfile - \
        wsgi:app 2>&1 | sed -e 's/^/[backend] /'
}

exec_frontend() {
    cd /app/frontend
    # `vite preview` serves the pre-built /dist on port 3000
    exec npx vite preview --host 0.0.0.0 --port "${FRONTEND_PORT:-3000}" 2>&1 \
        | sed -e 's/^/[frontend] /'
}

# Run gunicorn in background; if it crashes the "wait -n" below returns.
exec_backend &
BACKEND_PID=$!

exec_frontend &
FRONTEND_PID=$!

# Wait for either child to exit; propagate its status.
wait -n "$BACKEND_PID" "$FRONTEND_PID"
status=$?
kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
exit "$status"
EOF
RUN chmod +x /app/entrypoint.sh

# Gunicorn / vite preview need to write to a few runtime dirs — create them
# with correct ownership so mirofish (non-root) can use them.
RUN mkdir -p /app/backend/uploads /app/backend/logs \
    && chown -R mirofish:mirofish /app/backend/uploads /app/backend/logs

USER mirofish

EXPOSE 3000 5001

# tini handles zombie reaping cleanly when we run two child processes
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/app/entrypoint.sh"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD curl -fsS "http://localhost:${FLASK_PORT:-5001}/health" \
        && curl -fsS "http://localhost:${FRONTEND_PORT:-3000}/" > /dev/null \
        || exit 1
