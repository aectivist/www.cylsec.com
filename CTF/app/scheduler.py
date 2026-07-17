"""Scheduled background tasks for Docker instance cleanup."""

import logging
from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)


def setup_scheduler(app):
    from app.docker_manager import DockerInstanceManager

    scheduler = BackgroundScheduler()
    docker_manager = DockerInstanceManager()

    def cleanup_task():
        with app.app_context():
            if not docker_manager.is_available():
                return
            count = docker_manager.cleanup_expired()
            if count:
                logger.info(f"Scheduler: removed {count} expired instance(s)")

    scheduler.add_job(cleanup_task, "interval", minutes=5, id="docker_cleanup")

    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started — cleanup runs every 5 minutes")

    return scheduler
