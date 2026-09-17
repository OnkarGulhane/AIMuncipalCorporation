#!/bin/sh
set -e

echo "[AI Case Manager] Running database migrations..."
alembic upgrade head || {
    echo "[AI Case Manager] Warning: Alembic migrations encountered an issue, proceeding with fallback table creation."
}

echo "[AI Case Manager] Starting FastAPI application server..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --workers "${UVICORN_WORKERS:-2}"
