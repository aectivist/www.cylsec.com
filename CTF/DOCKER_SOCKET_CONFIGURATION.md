# Docker Socket Configuration Fix

## Problem

When running CYLVERN in Docker Compose, the Docker instance spawner was failing with:

```
❌ Failed to initialize Docker: Error while fetching server API version: Not supported URL scheme http+docker
```

## Root Cause

The Flask application running in Docker couldn't connect to the Docker daemon because:

1. Docker socket wasn't mounted into the container
2. User permissions weren't set up for Docker socket access
3. Docker client initialization wasn't handling multiple connection methods

## Solution Implemented

### 1. **Docker Compose** (`docker-compose.yml`)

Added Docker socket mounting:

```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock # Mount Docker socket
```

Added Docker host environment variable:

```yaml
environment:
  - DOCKER_HOST=unix:///var/run/docker.sock
```

Added port range for spawned instances:

```yaml
ports:
  - "9000-10000:9000-10000" # Port range for CTF instances
```

### 2. **Docker Manager** (`app/docker_manager.py`)

Enhanced initialization with fallback methods:

```python
# Try explicit Docker host if provided
if docker_host:
    self.client = docker.DockerClient(base_url=docker_host)

# Try socket file if it exists
elif os.path.exists(docker_socket):
    self.client = docker.DockerClient(base_url=f'unix://{docker_socket}')

# Try default from_env() method
else:
    self.client = docker.from_env()
```

### 3. **Dockerfile** (`Dockerfile`)

- Added `docker.io` package for Docker CLI tools
- Added user to docker group for socket permissions
- Proper group ID handling (GID 999 is typically docker)

## Deployment

### Local Docker Compose

```bash
docker-compose up --build
```

### Kubernetes/Production

If running in Kubernetes:

```yaml
volumeMounts:
  - name: docker-socket
    mountPath: /var/run/docker.sock
volumes:
  - name: docker-socket
    hostPath:
      path: /var/run/docker.sock
```

### Environment Variables

Optional configuration via `.env`:

```
DOCKER_HOST=unix:///var/run/docker.sock
DOCKER_SOCKET=/var/run/docker.sock
```

## Testing

### 1. Verify Docker Connection in Container

```bash
# Inside container
docker ps
docker --version
```

### 2. Check Python Docker Library

```python
import docker
client = docker.from_env()
client.ping()  # Should return True
```

### 3. Test Instance Spawning

```python
from app.docker_manager import DockerInstanceManager
manager = DockerInstanceManager()
print(f"Docker available: {manager.is_available()}")
```

## Troubleshooting

### "Permission denied" on docker.sock

```bash
# On host machine, ensure docker group exists
sudo usermod -aG docker $USER

# Rebuild container
docker-compose up --build
```

### Container can't connect to Docker daemon

1. Ensure `/var/run/docker.sock` exists on host
2. Check docker daemon is running: `docker ps`
3. Verify socket permissions: `ls -la /var/run/docker.sock`
4. Check docker-compose volume mount is correct

### Docker client initialization warnings

If you see warnings but Docker still works, it's OK - the fallback methods are working.

## Architecture

```
Host Machine
  └── /var/run/docker.sock (Docker daemon)
        ↓ (mounted)
  Docker Container (CYLVERN Flask app)
    └── /var/run/docker.sock (read-only access)
        ↓ (used by docker-py library)
  Docker API
    └── Spawn CTF challenge containers
```

## Security Notes

1. **Socket Mounting**: Mounting the Docker socket gives the container full Docker access
   - Be cautious in multi-tenant environments
   - Consider using Docker API security options if needed

2. **User Permissions**: The app user is added to docker group for socket access
   - This is necessary for the Python docker library to function
   - Not ideal for production multi-tenant systems

3. **Port Ranges**: CTF instances use ports 9000-10000
   - These must be exposed in docker-compose.yml
   - Adjust if there are conflicts

## References

- [Docker Python SDK Documentation](https://docker-py.readthedocs.io/)
- [Docker Socket Mounting](https://docs.docker.com/engine/security/rootless/)
- [Docker Compose Volumes](https://docs.docker.com/compose/compose-file/compose-file-v3/#volumes)
