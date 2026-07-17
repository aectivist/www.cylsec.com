"""Flask blueprint for managing Docker instances."""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app import db, csrf
from app.models import DockerInstance, Challenge
from app.docker_manager import DockerInstanceManager

docker_bp = Blueprint('docker', __name__, url_prefix='/docker')
docker_manager = DockerInstanceManager()


@docker_bp.before_request
def check_docker_available():
    """Warn if Docker is not available."""
    if not docker_manager.is_available():
        pass  # Handled per-route with user-facing messages


@docker_bp.route('/launch/<int:challenge_id>', methods=['GET', 'POST'])
@login_required
def launch_instance(challenge_id):
    """Launch a new Docker instance for a challenge."""
    challenge = Challenge.query.get_or_404(challenge_id)

    # Only instance-backed challenges can be launched
    if not challenge.instance_name:
        flash('This challenge does not have a launchable instance.', 'warning')
        return redirect(url_for('challenges.view_challenge', challenge_id=challenge_id))

    # Check if user already has an active instance for this challenge
    existing = DockerInstance.query.filter_by(
        user_id=current_user.id,
        challenge_id=challenge_id,
        is_active=True
    ).filter(DockerInstance.expires_at > datetime.utcnow()).first()

    if existing:
        flash('You already have an active instance for this challenge.', 'info')
        return redirect(url_for('docker.instance_detail', instance_id=existing.id))

    if request.method == 'POST':
        if not docker_manager.is_available():
            flash('Docker service is currently unavailable. Please try again later.', 'danger')
            return redirect(url_for('challenges.view_challenge', challenge_id=challenge_id))

        # Derive image name from challenge instance_name: cylvern/<instance_name>
        image_name = f"cylvern/{challenge.instance_name}"

        instance = docker_manager.spawn_instance(
            user_id=current_user.id,
            challenge_id=challenge_id,
            duration_minutes=60,
            image_name=image_name,
        )

        if instance:
            flash(f'✅ Instance launched! Access at {instance.url}', 'success')
            return redirect(url_for('docker.instance_detail', instance_id=instance.id))
        else:
            flash(
                f'Failed to launch instance. Ensure the Docker image "{image_name}" has been built.',
                'danger',
            )
            return redirect(url_for('challenges.view_challenge', challenge_id=challenge_id))

    return render_template('docker/launch.html', challenge=challenge)


@docker_bp.route('/instance/<int:instance_id>')
@login_required
def instance_detail(instance_id):
    """View details of a running instance."""
    instance = DockerInstance.query.get_or_404(instance_id)

    # Verify ownership
    if instance.user_id != current_user.id:
        flash('You do not have permission to view this instance.', 'danger')
        return redirect(url_for('main.index'))

    # Check if expired
    if instance.is_expired():
        instance.is_active = False
        db.session.commit()
        docker_manager.stop_instance(instance_id)
        flash('This instance has expired.', 'warning')
        return redirect(url_for('challenges.view_challenge', challenge_id=instance.challenge_id))

    info = docker_manager.get_instance_info(instance_id)
    return render_template('docker/instance_detail.html', instance=instance, info=info)


@docker_bp.route('/instance/<int:instance_id>/extend', methods=['POST'])
@login_required
def extend_instance(instance_id):
    """Extend the lifetime of an instance (AJAX)."""
    instance = DockerInstance.query.get_or_404(instance_id)

    # Verify ownership
    if instance.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    if not instance.can_extend():
        return jsonify({'error': 'Max extensions reached'}), 400

    extended = docker_manager.extend_instance(instance_id, duration_minutes=30)
    if extended:
        return jsonify({
            'success': True,
            'new_expiry': extended.expires_at.isoformat(),
            'time_remaining': extended.time_remaining(),
        })
    else:
        return jsonify({'error': 'Failed to extend instance'}), 500


@docker_bp.route('/instance/<int:instance_id>/stop', methods=['POST'])
@login_required
def stop_instance(instance_id):
    """Stop and remove an instance."""
    instance = DockerInstance.query.get_or_404(instance_id)

    # Verify ownership
    if instance.user_id != current_user.id:
        flash('You do not have permission to stop this instance.', 'danger')
        return redirect(url_for('docker.instance_detail', instance_id=instance_id))

    challenge_id = instance.challenge_id
    if docker_manager.stop_instance(instance_id):
        flash('Instance stopped successfully.', 'success')
    else:
        flash('Failed to stop instance.', 'danger')

    return redirect(url_for('challenges.view_challenge', challenge_id=challenge_id))


@docker_bp.route('/instances')
@login_required
def my_instances():
    """View all user's active instances."""
    instances = DockerInstance.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).filter(DockerInstance.expires_at > datetime.utcnow()).all()

    # Clean up expired ones in the background
    expired = DockerInstance.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).filter(DockerInstance.expires_at <= datetime.utcnow()).all()

    for exp in expired:
        docker_manager.stop_instance(exp.id)

    return render_template('docker/my_instances.html', instances=instances)


@docker_bp.route('/api/cleanup', methods=['POST'])
@csrf.exempt
def api_cleanup():
    """
    Background endpoint to clean up expired instances.
    Protected by API key in production via X-Cleanup-Token header.
    """
    api_key = request.headers.get('X-Cleanup-Token', '')
    import os
    expected = os.environ.get('CLEANUP_API_KEY', '')
    if expected and api_key != expected:
        return jsonify({'error': 'Unauthorized'}), 403

    count = docker_manager.cleanup_expired()
    return jsonify({'cleaned_up': count})
