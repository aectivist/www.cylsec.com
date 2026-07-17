#!/bin/sh
set -e
exec gunicorn \
    --bind 127.0.0.1:5001 \
    --workers 2 \
    --timeout 120 \
    "app:app"
