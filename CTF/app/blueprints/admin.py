import pyotp
import qrcode
import io
import base64
import logging
from flask import Blueprint, session, make_response, render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_required, current_user
from flask_mail import Message
from app import db, mail
from app.models import User, Category, Challenge, AdminLog, Solve, Setting
from app.admin_forms import ChallengeForm, CategoryForm, SystemSettingsForm
from app.instance_manager import get_available_instances

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
logger = logging.getLogger(__name__)


def admin_required(f):
    from functools import wraps
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated


# ── 2FA ──────────────────────────────────────────────────────────────────────

@admin_bp.route('/enable-2fa', methods=['GET', 'POST'])
@admin_required
def enable_2fa():
    if request.method == 'POST':
        token = request.form.get('token', '').strip()
        secret = session.get('totp_secret_pending')
        if not secret:
            flash('Session expired. Please try again.', 'danger')
            return redirect(url_for('admin.enable_2fa'))
        totp = pyotp.TOTP(secret)
        if totp.verify(token):
            current_user.totp_secret = secret
            current_user.two_factor_enabled = True
            db.session.commit()
            session.pop('totp_secret_pending', None)
            flash('2FA enabled successfully.', 'success')
            return redirect(url_for('admin.dashboard'))
        flash('Invalid code. Please try again.', 'danger')

    secret = pyotp.random_base32()
    session['totp_secret_pending'] = secret
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=current_user.email, issuer_name='CYLVERN Security')
    qr = qrcode.make(uri)
    buf = io.BytesIO()
    qr.save(buf, format='PNG')
    qr_b64 = base64.b64encode(buf.getvalue()).decode()
    return render_template('admin/enable_2fa.html', secret=secret, qr_b64=qr_b64)


@admin_bp.route('/verify-2fa', methods=['GET', 'POST'])
@login_required
def verify_2fa():
    if request.method == 'POST':
        token = request.form.get('token', '').strip()
        if current_user.totp_secret:
            totp = pyotp.TOTP(current_user.totp_secret)
            if totp.verify(token):
                session['2fa_verified'] = True
                return redirect(url_for('admin.dashboard'))
        flash('Invalid code.', 'danger')
    return render_template('admin/verify_2fa.html')


@admin_bp.route('/disable-2fa', methods=['POST'])
@admin_required
def disable_2fa():
    current_user.two_factor_enabled = False
    current_user.totp_secret = None
    db.session.commit()
    flash('2FA disabled.', 'info')
    return redirect(url_for('admin.dashboard'))


# ── Dashboard ─────────────────────────────────────────────────────────────────

@admin_bp.route('/')
@admin_bp.route('/admin')
@admin_required
def dashboard():
    users = User.query.order_by(User.xp.desc()).all()
    challenges = Challenge.query.all()
    categories = Category.query.all()
    total_solves = Solve.query.count()
    return render_template('admin/dashboard.html',
                           users=users, challenges=challenges,
                           categories=categories, total_solves=total_solves)


# ── Challenges ────────────────────────────────────────────────────────────────

@admin_bp.route('/challenges')
@admin_required
def list_challenges():
    challenges = Challenge.query.order_by(Challenge.id.desc()).all()
    return render_template('admin/challenges.html', challenges=challenges)


@admin_bp.route('/challenges/add', methods=['GET', 'POST'])
@admin_required
def add_challenge():
    form = ChallengeForm()
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]
    form.update_instance_choices()

    if form.validate_on_submit():
        challenge = Challenge(
            category_id=form.category_id.data,
            title=form.title.data,
            description=form.description.data,
            difficulty=form.difficulty.data,
            points=form.points.data,
            flag=form.flag.data,
            is_active=form.is_active.data,
            type=form.type.data,
            file_url=form.file_url.data or None,
            challenge_url=form.challenge_url.data or None,
            instance_name=form.instance_name.data or None,
        )
        db.session.add(challenge)
        db.session.commit()
        _log(f'Created challenge: {challenge.title}')
        flash(f'Challenge "{challenge.title}" created.', 'success')
        return redirect(url_for('admin.list_challenges'))

    return render_template('admin/challenge_form.html', form=form, title='Add Challenge')


@admin_bp.route('/challenges/edit/<int:challenge_id>', methods=['GET', 'POST'])
@admin_required
def edit_challenge(challenge_id):
    challenge = Challenge.query.get_or_404(challenge_id)
    form = ChallengeForm(obj=challenge)
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]
    form.update_instance_choices()

    if form.validate_on_submit():
        challenge.category_id = form.category_id.data
        challenge.title = form.title.data
        challenge.description = form.description.data
        challenge.difficulty = form.difficulty.data
        challenge.points = form.points.data
        challenge.flag = form.flag.data
        challenge.is_active = form.is_active.data
        challenge.type = form.type.data
        challenge.file_url = form.file_url.data or None
        challenge.challenge_url = form.challenge_url.data or None
        challenge.instance_name = form.instance_name.data or None
        db.session.commit()
        _log(f'Edited challenge: {challenge.title}')
        flash(f'Challenge "{challenge.title}" updated.', 'success')
        return redirect(url_for('admin.list_challenges'))

    return render_template('admin/challenge_form.html', form=form, title='Edit Challenge', challenge=challenge)


@admin_bp.route('/challenges/delete/<int:challenge_id>', methods=['POST'])
@admin_required
def delete_challenge(challenge_id):
    challenge = Challenge.query.get_or_404(challenge_id)
    title = challenge.title
    db.session.delete(challenge)
    db.session.commit()
    _log(f'Deleted challenge: {title}')
    flash(f'Challenge "{title}" deleted.', 'success')
    return redirect(url_for('admin.list_challenges'))


# ── Categories ────────────────────────────────────────────────────────────────

@admin_bp.route('/categories')
@admin_required
def list_categories():
    categories = Category.query.all()
    return render_template('admin/categories.html', categories=categories)


@admin_bp.route('/categories/add', methods=['GET', 'POST'])
@admin_required
def add_category():
    form = CategoryForm()
    if form.validate_on_submit():
        cat = Category(name=form.name.data, description=form.description.data)
        db.session.add(cat)
        db.session.commit()
        flash(f'Category "{cat.name}" created.', 'success')
        return redirect(url_for('admin.list_categories'))
    return render_template('admin/category_form.html', form=form, title='Add Category')


@admin_bp.route('/categories/edit/<int:category_id>', methods=['GET', 'POST'])
@admin_required
def edit_category(category_id):
    cat = Category.query.get_or_404(category_id)
    form = CategoryForm(obj=cat)
    if form.validate_on_submit():
        cat.name = form.name.data
        cat.description = form.description.data
        db.session.commit()
        flash(f'Category "{cat.name}" updated.', 'success')
        return redirect(url_for('admin.list_categories'))
    return render_template('admin/category_form.html', form=form, title='Edit Category', category=cat)


@admin_bp.route('/categories/delete/<int:category_id>', methods=['POST'])
@admin_required
def delete_category(category_id):
    cat = Category.query.get_or_404(category_id)
    name = cat.name
    db.session.delete(cat)
    db.session.commit()
    flash(f'Category "{name}" deleted.', 'success')
    return redirect(url_for('admin.list_categories'))


# ── Users ─────────────────────────────────────────────────────────────────────

@admin_bp.route('/users')
@admin_required
def list_users():
    users = User.query.order_by(User.xp.desc()).all()
    return render_template('admin/users.html', users=users)


@admin_bp.route('/users/toggle_admin/<int:user_id>', methods=['POST'])
@admin_required
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Cannot modify your own admin status.', 'danger')
        return redirect(url_for('admin.list_users'))
    user.role = 'user' if user.role == 'admin' else 'admin'
    db.session.commit()
    flash(f'Updated role for {user.username}.', 'success')
    return redirect(url_for('admin.list_users'))


@admin_bp.route('/users/update_xp/<int:user_id>', methods=['POST'])
@admin_required
def update_xp(user_id):
    user = User.query.get_or_404(user_id)
    try:
        user.xp = int(request.form.get('xp', user.xp))
        db.session.commit()
        flash(f'XP updated for {user.username}.', 'success')
    except ValueError:
        flash('Invalid XP value.', 'danger')
    return redirect(url_for('admin.list_users'))


@admin_bp.route('/users/update_rank/<int:user_id>', methods=['POST'])
@admin_required
def update_rank(user_id):
    user = User.query.get_or_404(user_id)
    user.custom_rank = request.form.get('rank', '').strip() or None
    user.rank_color = request.form.get('rank_color', '').strip() or None
    db.session.commit()
    flash(f'Rank updated for {user.username}.', 'success')
    return redirect(url_for('admin.list_users'))


@admin_bp.route('/users/set_role/<int:user_id>', methods=['POST'])
@admin_required
def set_role(user_id):
    user = User.query.get_or_404(user_id)
    role = request.form.get('role', 'user')
    if role in ('admin', 'maker', 'user'):
        user.role = role
        db.session.commit()
        flash(f'Role updated for {user.username}.', 'success')
    return redirect(url_for('admin.list_users'))


@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Cannot delete your own account.', 'danger')
        return redirect(url_for('admin.list_users'))
    username = user.username
    db.session.delete(user)
    db.session.commit()
    flash(f'User "{username}" deleted.', 'success')
    return redirect(url_for('admin.list_users'))


# ── API ───────────────────────────────────────────────────────────────────────

@admin_bp.route('/api/instances/<challenge_type>')
@admin_required
def api_instances(challenge_type):
    from flask import jsonify
    instances = get_available_instances(challenge_type)
    return jsonify(instances)


# ── Settings ──────────────────────────────────────────────────────────────────

@admin_bp.route('/settings', methods=['GET', 'POST'])
@admin_required
def settings():
    form = SystemSettingsForm()
    if form.validate_on_submit():
        Setting.set('system_log_message', form.system_log_message.data)
        flash('Settings saved.', 'success')
        return redirect(url_for('admin.settings'))
    form.system_log_message.data = Setting.get('system_log_message', '')
    return render_template('admin/settings.html', form=form)


# ── helpers ───────────────────────────────────────────────────────────────────

def _log(action, details=None):
    try:
        log = AdminLog(
            admin_id=current_user.id,
            action=action,
            details=details,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')[:200],
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        logger.error(f'Failed to write admin log: {e}')
