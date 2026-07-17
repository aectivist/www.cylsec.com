#!/bin/bash
set -e

echo "[entrypoint] Running database migrations..."
flask db upgrade

echo "[entrypoint] Seeding database..."
python seed.py || true

echo "[entrypoint] Starting application..."
exec gunicorn \
    --bind 127.0.0.1:5000 \
    --workers 2 \
    --timeout 120 \
    "app:create_app()"
