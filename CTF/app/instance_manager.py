"""
Utility to enumerate available Docker challenge images.
Returns a list of image name strings that can be selected for a challenge.
"""
import os
import logging

logger = logging.getLogger(__name__)


def get_available_instances(challenge_type=None):
    """
    Return a list of available Docker image names for challenge instances.
    Tries to query the local Docker daemon; falls back to empty list if
    Docker is not available.
    """
    try:
        import docker
        client = docker.from_env()
        images = client.images.list()
        names = []
        for img in images:
            for tag in img.tags:
                # Only include cylvern/ prefixed images
                if tag.startswith('cylvern/'):
                    name = tag.split('cylvern/')[-1].split(':')[0]
                    if name and name not in names:
                        names.append(name)
        return sorted(names)
    except Exception as e:
        logger.debug(f'Docker not available for instance listing: {e}')
        return []
