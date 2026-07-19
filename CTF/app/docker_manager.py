"""
Docker instance manager for CTF challenges.
Handles spawning, extending, stopping, and cleaning up containers.
"""
import os
import logging
from datetime import datetime, timedelta
from app import db
from app.models import DockerInstance

logger = logging.getLogger(__name__)

INSTANCE_HOST = os.environ.get('INSTANCE_HOST', 'localhost')
PORT_RANGE_START = int(os.environ.get('PORT_RANGE_START', 10000))
PORT_RANGE_END   = int(os.environ.get('PORT_RANGE_END',   11000))


def _get_client():
    try:
        import docker
        return docker.from_env()
    except Exception as e:
        logger.warning(f'Docker client unavailable: {e}')
        return None


def _next_free_port():
    used = {r[0] for r in db.session.query(DockerInstance.port)
            .filter_by(is_active=True).all()}
    for p in range(PORT_RANGE_START, PORT_RANGE_END):
        if p not in used:
            return p
    return None


class DockerInstanceManager:

    def is_available(self):
        return _get_client() is not None

    def spawn_instance(self, user_id, challenge_id, duration_minutes=15, image_name=None):
        client = _get_client()
        if not client or not image_name:
            return None

        # Allow only one launch per challenge per user per day
        start_of_day = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        end_of_day = start_of_day + timedelta(days=1)

        existing = (
            DockerInstance.query
            .filter(
                DockerInstance.user_id == user_id,
                DockerInstance.challenge_id == challenge_id,
                DockerInstance.created_at >= start_of_day,
                DockerInstance.created_at < end_of_day,
            )
            .first()
        )

        if existing:
            logger.info(
                f"User {user_id} already launched challenge {challenge_id} today."
            )
            return None

        port = _next_free_port()
        if port is None:
            logger.error('No free ports available for Docker instance')
            return None

        try:
            container = client.containers.run(
                image_name,
                detach=True,
                ports={'5000/tcp': port},
                labels={
                    'cylvern.user_id': str(user_id),
                    'cylvern.challenge_id': str(challenge_id),
                },
                remove=False,
            )
            expires_at = datetime.utcnow() + timedelta(minutes=duration_minutes)
            instance = DockerInstance(
                user_id=user_id,
                challenge_id=challenge_id,
                container_id=container.id,
                port=port,
                expires_at=expires_at,
                is_active=True,
                url=f'http://{INSTANCE_HOST}:{port}',
            )
            db.session.add(instance)
            db.session.commit()
            return instance
        except Exception as e:
            logger.error(f'Failed to spawn Docker instance: {e}')
            return None

    def extend_instance(self, instance_id, duration_minutes=30):
        instance = DockerInstance.query.get(instance_id)
        if not instance:
            return None
        instance.expires_at += timedelta(minutes=duration_minutes)
        instance.extensions_used += 1
        instance.last_extended_at = datetime.utcnow()
        db.session.commit()
        return instance

    def stop_instance(self, instance_id):
        instance = DockerInstance.query.get(instance_id)
        if not instance:
            return False
        client = _get_client()
        if client:
            try:
                container = client.containers.get(instance.container_id)
                container.stop(timeout=5)
                container.remove(force=True)
            except Exception as e:
                logger.warning(f'Error stopping container {instance.container_id}: {e}')
        instance.is_active = False
        db.session.commit()
        return True

    def get_instance_info(self, instance_id):
        instance = DockerInstance.query.get(instance_id)
        if not instance:
            return {}
        client = _get_client()
        container_status = 'unknown'
        if client:
            try:
                container = client.containers.get(instance.container_id)
                container_status = container.status
            except Exception:
                container_status = 'not found'
        return {
            'container_status': container_status,
            'time_remaining_seconds': instance.time_remaining(),
            'expires_at': instance.expires_at.strftime('%Y-%m-%d %H:%M UTC'),
            'can_extend': instance.can_extend(),
        }

    def cleanup_expired(self):
        expired = (DockerInstance.query
                   .filter_by(is_active=True)
                   .filter(DockerInstance.expires_at < datetime.utcnow())
                   .all())
        count = 0
        for inst in expired:
            if self.stop_instance(inst.id):
                count += 1
        return count
