# Use Python slim image for smaller size
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=run.py \
    FLASK_ENV=production

# Install system dependencies (including docker client for debugging, optional)
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (better layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project
COPY . .

# Copy entrypoint script with executable permission
COPY --chmod=755 entrypoint.sh /entrypoint.sh

# Create a non-root user and set ownership
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser:appuser /app

# Add appuser to docker group (for Docker socket access)
RUN groupadd -f -g 999 docker && usermod -aG docker appuser

USER appuser

# Expose port
EXPOSE 8000

# Use the entrypoint script
ENTRYPOINT ["/entrypoint.sh"]