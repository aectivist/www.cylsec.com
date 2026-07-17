FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=run.py \
    FLASK_ENV=production

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY --chmod=755 entrypoint.sh /entrypoint.sh

RUN adduser --disabled-password --gecos '' appuser && chown -R appuser:appuser /app
RUN groupadd -f -g 999 docker && usermod -aG docker appuser

USER appuser

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
