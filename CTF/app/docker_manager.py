"""Docker instance manager — uses the Docker CLI via subprocess.

docker-py 6.x has a broken http+docker:// transport on Windows (requests 2.32+
rejects custom URL schemes).  The Docker CLI itself works fine on the same
machine, so every operation is delegated to it via subprocess.
"""

import logging
import os
import shutil
import socket
import subprocess
from datetime import datetime, timedelta

from app import db
from app.models import DockerInstance, Challenge

logger = logging.getLogger(__name__)

_DOCKER_EXE = shutil.which("docker") or "docker"


def _run(args, *, timeout=30):
    """Run a docker CLI command, return (returncode, stdout, stderr)."""
    cmd = [_DOCKER_EXE] + args
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except FileNotFoundError:
        return 1, "", "docker executable not found on PATH"
    except subprocess.TimeoutExpired:
        return 1, "", f"docker command timed out after {timeout}s"
    except Exception as e:
        return 1, "", str(e)


def _port_in_use(port: int) -> bool:
    """Return True if *port* is already bound on the host."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.2)
        try:
            s.connect(("127.0.0.1", port))
            return True
        except (ConnectionRefusedError, OSError):
            return False


class DockerInstanceManager:
    """Manages lifecycle of temporary Docker containers for CTF challenges."""

    def is_available(self) -> bool:
        """Return True when the Docker daemon is reachable via the CLI."""
        rc, _, _ = _run(["info", "--format", "{{.ServerVersion}}"], timeout=8)
        return rc == 0

    def spawn_instance(
        self,
        user_id: int,
        challenge_id: int,
        duration_minutes: int = 60,
        image_name: str = None,
        port: int = None,
        internal_port: int = 80,
    ):
        if not self.is_available():
            logger.error("Docker daemon is not reachable")
            return None

        challenge = Challenge.query.get(challenge_id)
        if not challenge:
            logger.error(f"Challenge {challenge_id} not found")
            return None

        if not image_name:
            image_name = (
                f"cylvern/{challenge.instance_name}"
                if challenge.instance_name
                else f"cylvern/challenge-{challenge.id}"
            )

        rc, _, _ = _run(["image", "inspect", image_name, "--format", "{{.Id}}"], timeout=10)
        if rc != 0:
            logger.error(
                f"Docker image '{image_name}' not found locally. "
                f"Build it with: docker build -t {image_name} <path>"
            )
            return None

        if port is None:
            port = self._find_available_port()
            if port is None:
                logger.error("No free port found in range 9000-10000")
                return None

        container_name = (
            f"cylvern-{user_id}-{challenge_id}-{int(datetime.utcnow().timestamp())}"
        )

        rc, stdout, stderr = _run(
            [
                "run", "-d",
                "--name", container_name,
                "-p", f"{port}:{internal_port}",
                "--memory", "512m",
                "--cpus", "1",
                "--network", "bridge",
                "--label", "cylvern=true",
                "--label", f"user_id={user_id}",
                "--label", f"challenge_id={challenge_id}",
                image_name,
            ],
            timeout=30,
        )

        if rc != 0:
            logger.error(f"docker run failed: {stderr}")
            return None

        container_id = stdout.strip()
        expires_at = datetime.utcnow() + timedelta(minutes=duration_minutes)
        instance_host = os.environ.get("INSTANCE_HOST", "localhost")
        url = f"http://{instance_host}:{port}"

        instance = DockerInstance(
            user_id=user_id,
            challenge_id=challenge_id,
            container_id=container_id,
            port=port,
            expires_at=expires_at,
            url=url,
        )
        db.session.add(instance)
        db.session.commit()

        logger.info(
            f"Spawned instance for user {user_id}, challenge {challenge_id} "
            f"on port {port} (container {container_id[:12]})"
        )
        return instance

    def extend_instance(self, instance_id: int, duration_minutes: int = 30):
        instance = DockerInstance.query.get(instance_id)
        if not instance:
            return None
        if instance.is_expired() or not instance.can_extend():
            return None
        try:
            base = max(instance.expires_at, datetime.utcnow())
            instance.expires_at = base + timedelta(minutes=duration_minutes)
            instance.extensions_used += 1
            instance.last_extended_at = datetime.utcnow()
            db.session.commit()
            return instance
        except Exception as e:
            logger.error(f"Failed to extend instance {instance_id}: {e}")
            return None

    def stop_instance(self, instance_id: int) -> bool:
        instance = DockerInstance.query.get(instance_id)
        if not instance:
            return False
        cid = instance.container_id
        _run(["stop", "--time", "5", cid], timeout=15)
        _run(["rm", "-f", cid], timeout=10)
        instance.is_active = False
        db.session.commit()
        logger.info(f"Stopped instance {instance_id} (container {cid[:12]})")
        return True

    def cleanup_expired(self) -> int:
        expired = DockerInstance.query.filter(
            DockerInstance.is_active == True,
            DockerInstance.expires_at < datetime.utcnow(),
        ).all()
        count = 0
        for inst in expired:
            if self.stop_instance(inst.id):
                count += 1
        if count:
            logger.info(f"Cleaned up {count} expired instance(s)")
        return count

    def get_instance_info(self, instance_id: int):
        instance = DockerInstance.query.get(instance_id)
        if not instance:
            return None
        info = {
            "id": instance.id,
            "url": instance.url,
            "port": instance.port,
            "expires_at": instance.expires_at.isoformat(),
            "time_remaining_seconds": instance.time_remaining(),
            "can_extend": instance.can_extend(),
            "extensions_used": instance.extensions_used,
            "container_status": "unknown",
        }
        rc, stdout, _ = _run(
            ["inspect", "--format", "{{.State.Status}}", instance.container_id],
            timeout=8,
        )
        if rc == 0 and stdout:
            info["container_status"] = stdout.strip()
        return info

    def _find_available_port(self, start_port: int = 9000, end_port: int = 10000):
        used_ports = {
            row.port
            for row in DockerInstance.query.filter_by(is_active=True)
            .with_entities(DockerInstance.port)
            .all()
        }
        for port in range(start_port, end_port):
            if port not in used_ports and not _port_in_use(port):
                return port
        return None
