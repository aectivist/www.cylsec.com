FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create a writable instance directory for SQLite at runtime
RUN mkdir -p /app/instance && chmod 777 /app/instance

# Remove any pre-committed database so the container always starts fresh
RUN rm -f /app/instance/ashal.db

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "60", "app:app"]
