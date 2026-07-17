#!/bin/sh
set -e
python -c "from app import init_db; init_db()"
exec gunicorn --bind 0.0.0.0:8001 --timeout 120 app:app
