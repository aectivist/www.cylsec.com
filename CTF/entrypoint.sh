#!/bin/bash
set -e

echo "[entrypoint] Initialising database tables..."
/root/www.cylsec.com/CTF/venv/bin/python3.11 -c "
from app import create_app, db
app = create_app()
with app.app_context():
    db.create_all()
    print('DB tables created/verified.')
"

echo "[entrypoint] Starting application..."
exec /root/www.cylsec.com/CTF/venv/bin/gunicorn \
    --bind 127.0.0.1:5000 \
    --workers 2 \
    --timeout 120 \
    --access-logfile /var/log/cylvern-ctf.access.log \
    --error-logfile /var/log/cylvern-ctf.error.log \
    "app:create_app()"
