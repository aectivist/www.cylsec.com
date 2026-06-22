#!/bin/sh
set -e

echo "Running database migrations..."
flask db upgrade

echo "Seeding database..."
python seed.py

echo "Starting Gunicorn..."
exec gunicorn --bind 0.0.0.0:8000 run:app