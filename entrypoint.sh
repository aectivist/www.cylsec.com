#!/bin/sh
set -e

echo "Running database migrations..."
flask db upgrade

echo "Checking if database is empty..."
# Check if any user exists
USER_COUNT=$(flask shell -c "from app.models import User; print(User.query.count())" 2>/dev/null || echo "0")
if [ "$USER_COUNT" -eq 0 ]; then
    echo "Database is empty – seeding initial data..."
    python seed.py
else
    echo "Database already contains data – skipping seed."
fi

echo "Starting Gunicorn..."
exec gunicorn --bind 0.0.0.0:8000 --timeout 120 run:app