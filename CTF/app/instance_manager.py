"""Utility for managing CTF instances (local Docker folders)."""

import os
from pathlib import Path

BASE_INSTANCES_PATH = Path(__file__).parent.parent / 'CTF_Instances'

INSTANCE_TYPES = {
    'web': 'Web_Instances',
    'pwn': 'Pwn_Instances',
    'forensics': 'Forensics_Instances',
    'rev': 'Rev_Instances',
    'crypto': 'Crypto_Instances',
    'osint': 'OSINT_Instances',
}


def get_available_instances(challenge_type):
    """
    Get all available instances for a challenge type.
    
    Args:
        challenge_type: 'web', 'pwn', 'rev', etc.
    
    Returns:
        List of instance folder names
    """
    if challenge_type not in INSTANCE_TYPES:
        return []
    
    type_folder = INSTANCE_TYPES[challenge_type]
    instances_path = BASE_INSTANCES_PATH / type_folder
    
    if not instances_path.exists():
        return []
    
    # Get all subdirectories
    instances = []
    for item in instances_path.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            instances.append(item.name)
    
    return sorted(instances)


def get_instance_path(challenge_type, instance_name):
    """
    Get the full path to an instance.
    
    Args:
        challenge_type: 'web', 'pwn', 'rev', etc.
        instance_name: folder name of the instance
    
    Returns:
        Path object to the instance, or None if not found
    """
    if challenge_type not in INSTANCE_TYPES:
        return None
    
    type_folder = INSTANCE_TYPES[challenge_type]
    instance_path = BASE_INSTANCES_PATH / type_folder / instance_name
    
    if instance_path.exists():
        return instance_path
    
    return None


def instance_exists(challenge_type, instance_name):
    """Check if an instance exists."""
    return get_instance_path(challenge_type, instance_name) is not None


def get_instance_dockerfile_path(challenge_type, instance_name):
    """
    Get the Dockerfile path for an instance if it exists.
    
    Returns:
        Path to Dockerfile, or None if not found
    """
    instance_path = get_instance_path(challenge_type, instance_name)
    if not instance_path:
        return None
    
    dockerfile_path = instance_path / 'Dockerfile'
    if dockerfile_path.exists():
        return dockerfile_path
    
    return None


def get_instance_app_path(challenge_type, instance_name):
    """
    Get the app.py path for an instance if it exists.
    
    Returns:
        Path to app.py, or None if not found
    """
    instance_path = get_instance_path(challenge_type, instance_name)
    if not instance_path:
        return None
    
    app_path = instance_path / 'app.py'
    if app_path.exists():
        return app_path
    
    return None


def list_all_instances():
    """Get all instances grouped by type."""
    all_instances = {}
    for challenge_type in INSTANCE_TYPES:
        instances = get_available_instances(challenge_type)
        if instances:
            all_instances[challenge_type] = instances
    
    return all_instances
