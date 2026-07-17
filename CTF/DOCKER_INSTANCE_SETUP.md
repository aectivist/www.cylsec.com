# Docker Instance Launcher - Setup Guide

## Overview

This system allows users to spawn temporary Docker containers for CTF challenges with:

- **Time limits** (default 60 minutes)
- **Extension capability** (max 3 extensions of 30 mins each)
- **Resource constraints** (512MB memory, 1 CPU core)
- **Auto-cleanup** (expired instances removed automatically)

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Update Database

Create migration for the new `docker_instances` table:

```bash
flask db migrate -m "Add DockerInstance model"
flask db upgrade
```

### 3. Build Docker Images

Create Dockerfiles for each challenge. Example:

**Dockerfile for a web challenge:**

```dockerfile
FROM node:18-alpine

WORKDIR /app
COPY . .
RUN npm install

EXPOSE 80
CMD ["npm", "start"]
```

Build and tag the image:

```bash
docker build -t cylvern/challenge-1 .
docker push your-registry/cylvern/challenge-1  # if using registry
```

### 4. Enable Background Scheduler (Optional)

Add to your `run.py`:

```python
from app.scheduler import setup_scheduler

if __name__ == '__main__':
    app = create_app()
    scheduler = setup_scheduler(app)
    app.run(debug=False, host='0.0.0.0', port=5000)
```

## Configuration

### Environment Variables

Add to `.env`:

```
# Docker settings
DOCKER_SOCKET=/var/run/docker.sock
DOCKER_INSTANCE_PORT_START=9000
DOCKER_INSTANCE_PORT_END=10000
DOCKER_INSTANCE_DURATION=60  # minutes
DOCKER_INSTANCE_MAX_MEMORY=512m  # memory limit
DOCKER_INSTANCE_MAX_EXTENSIONS=3
```

### Challenge Model Enhancement

Add to `Challenge` model to track which challenges support Docker:

```python
supports_docker = db.Column(db.Boolean, default=False)
docker_image = db.Column(db.String(255), nullable=True)
```

## Usage

### User Flow

1. **View Challenge** → Click "Launch Instance"
2. **Launch Page** → Confirm resource usage → Click "Launch Instance"
3. **Instance Page** → Access via URL or extend/stop
4. **Management** → View all active instances, extend before expiry
5. **Cleanup** → Auto-stops when time expires

### Admin Flow

1. **Create Challenge** → Set `supports_docker=True`
2. **Specify Image** → Set `docker_image` field
3. **Monitor** → View active instances in admin panel
4. **Cleanup** → Automatic via scheduler or manual via API

### API Endpoints

```
POST   /docker/launch/<challenge_id>          # Launch instance
GET    /docker/instance/<instance_id>        # View instance details
POST   /docker/instance/<instance_id>/extend  # Extend time
POST   /docker/instance/<instance_id>/stop    # Stop instance
GET    /docker/instances                      # List user's instances
POST   /docker/api/cleanup                    # Manual cleanup (admin)
```

## Example Docker Images

### Web Challenge (Node.js)

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY . .
RUN npm install
EXPOSE 80
CMD ["npm", "start"]
```

### Python Web App

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 80
CMD ["python", "app.py"]
```

### CTF Binary Challenge

```dockerfile
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y xinetd
WORKDIR /app
COPY binary /app/binary
COPY service /etc/xinetd.d/service
RUN chmod +x /app/binary
EXPOSE 9000
CMD ["/etc/init.d/xinetd", "start", "-D"]
```

## Monitoring & Cleanup

### Manual Cleanup

```bash
curl -X POST http://localhost:5000/docker/api/cleanup
```

### View Active Instances

```bash
# Get all instances via API
SELECT * FROM docker_instances WHERE is_active = true AND expires_at > NOW();
```

### Docker Container Status

```bash
# List all Cylvern containers
docker ps --filter "label=cylvern=true"

# View container logs
docker logs <container_id>

# Stop specific container
docker stop <container_id>
```

## Security Considerations

1. **Resource Limits**: Each container limited to 512MB memory & 1 CPU
2. **Network Isolation**: Containers run in bridge network (isolated)
3. **Port Management**: Each gets unique port (9000-10000 range)
4. **User Verification**: Users can only access their own instances
5. **Auto-Cleanup**: Expired containers automatically removed
6. **Log Isolation**: Container logs don't leak between users

## Troubleshooting

### "Docker is not available" Error

```bash
# Check if Docker daemon is running
docker ps

# Verify socket permissions
sudo usermod -aG docker $USER
```

### Container Won't Start

```bash
# Check image exists
docker images | grep cylvern

# Check image is accessible
docker pull cylvern/challenge-1

# View container logs
docker logs <container_id>
```

### Port Conflicts

The system auto-selects ports 9000-10000. If needed, change in `docker_manager.py`:

```python
def _find_available_port(self, start_port=9000, end_port=10000):
    # Modify these ranges
```

### Memory Issues

Reduce per-container memory in `docker_manager.py`:

```python
memory='256m',  # Instead of 512m
```

## Advanced: Scaling with Docker Compose

For production, use Docker Compose to manage the full stack:

```yaml
version: "3.8"
services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  postgres:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: postgres
    volumes:
      - db_data:/var/lib/postgresql/data

volumes:
  db_data:
```

## Next Steps

1. ✅ Install docker Python package
2. ✅ Create migration for docker_instances table
3. ✅ Build Docker images for challenges
4. ✅ Test instance spawning locally
5. ✅ Set up background scheduler
6. ✅ Configure resource limits
7. ✅ Test extension/cleanup flows
8. ✅ Deploy to production
