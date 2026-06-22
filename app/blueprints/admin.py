import pyotp
import qrcode
import io
import base64
import logging
from flask import session, make_response, Blueprint, render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_required, current_user
from flask_mail import Message
from app import db, mail
from app.models import User, Category, Challenge, AdminLog, Solve, Setting
from app.admin_forms import ChallengeForm, CategoryForm, SystemSettingsForm

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
logger = logging.getLogger(__name__)


# ---------- DECORATORS ----------

def admin_required(f):
    """Restrict access to users with role='admin'."""
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated


def maker_required(f):
    """Restrict access to users with role='admin' or 'maker'."""
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['admin', 'maker']:
            abort(403)
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated


def admin_2fa_required(f):
    """Require TOTP 2FA verification for admin routes."""
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)
        if current_user.totp_secret and not session.get('2fa_verified'):
            flash('Please verify your identity with 2FA.', 'warning')
            return redirect(url_for('admin.verify_2fa_login'))
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated


# ---------- HELPER FUNCTIONS ----------

def send_admin_alert(subject, body):
    """Send an email alert to the configured admin email."""
    with current_app.app_context():
        msg = Message(
            subject=f"[CYLVERN ADMIN] {subject}",
            sender=current_app.config['MAIL_USERNAME'],
            recipients=[current_app.config['ADMIN_ALERT_EMAIL']]
        )
        msg.body = body
        try:
            mail.send(msg)
            logger.info(f"Admin alert email sent: {subject}")
        except Exception as e:
            logger.error(f"Failed to send admin alert email: {e}")


def log_admin_action(action, details=None):
    """Log an admin action with IP and user agent."""
    ip = request.remote_addr
    ua = request.headers.get('User-Agent')
    log = AdminLog(
        admin_id=current_user.id,
        action=action,
        details=details,
        ip_address=ip,
        user_agent=ua
    )
    db.session.add(log)
    db.session.commit()


def get_totp(user):
    """Return a TOTP object if secret exists, else None."""
    if not user.totp_secret:
        return None
    return pyotp.TOTP(user.totp_secret)


# ---------- 2FA MANAGEMENT ROUTES ----------

@admin_bp.route('/enable-2fa', methods=['GET'])
@login_required
@admin_required
def enable_2fa():
    if current_user.totp_secret:
        flash('2FA is already enabled.', 'info')
        return redirect(url_for('admin.dashboard'))
    secret = pyotp.random_base32()
    session['temp_totp_secret'] = secret
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=current_user.email, issuer_name="CYLVERN Security")
    img = qrcode.make(uri)
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return render_template('admin/enable_2fa.html', secret=secret, qr_code=img_str)


@admin_bp.route('/verify-2fa', methods=['POST'])
@login_required
@admin_required
def verify_2fa():
    code = request.form.get('code', '').strip()
    if not code:
        flash('Please enter the verification code.', 'danger')
        return redirect(url_for('admin.enable_2fa'))
    if current_user.totp_secret:
        totp = pyotp.TOTP(current_user.totp_secret)
        if totp.verify(code):
            session['2fa_verified'] = True
            flash('2FA verified.', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid verification code.', 'danger')
            return render_template('admin/verify_2fa.html')
    temp_secret = session.get('temp_totp_secret')
    if not temp_secret:
        flash('No 2FA setup in progress.', 'danger')
        return redirect(url_for('admin.dashboard'))
    totp = pyotp.TOTP(temp_secret)
    if totp.verify(code):
        current_user.totp_secret = temp_secret
        db.session.commit()
        session.pop('temp_totp_secret', None)
        session['2fa_verified'] = True
        flash('2FA enabled successfully!', 'success')
        return redirect(url_for('admin.dashboard'))
    else:
        flash('Invalid verification code. Please try again.', 'danger')
        return render_template('admin/enable_2fa.html', secret=temp_secret, qr_code=request.args.get('qr_code'))


@admin_bp.route('/verify-2fa-login', methods=['GET', 'POST'])
@login_required
@admin_required
def verify_2fa_login():
    if current_user.role != 'admin' or not current_user.totp_secret:
        return redirect(url_for('admin.dashboard'))
    if session.get('2fa_verified'):
        return redirect(url_for('admin.dashboard'))
    if request.method == 'POST':
        code = request.form.get('code')
        totp = pyotp.TOTP(current_user.totp_secret)
        if totp.verify(code):
            session['2fa_verified'] = True
            flash('2FA verified.', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid code.', 'danger')
    return render_template('admin/verify_2fa.html')


@admin_bp.route('/disable-2fa', methods=['POST'])
@login_required
@admin_required
def disable_2fa():
    current_user.totp_secret = None
    db.session.commit()
    session.pop('2fa_verified', None)
    flash('2FA has been disabled.', 'success')
    return redirect(url_for('admin.dashboard'))


# ---------- DASHBOARD (admin only, 2FA required) ----------

@admin_bp.route('/')
@login_required
@admin_2fa_required
def dashboard():
    stats = {
        'users': User.query.count(),
        'categories': Category.query.count(),
        'challenges': Challenge.query.count(),
        'active_challenges': Challenge.query.filter_by(is_active=True).count()
    }
    recent_logs = AdminLog.query.order_by(AdminLog.timestamp.desc()).limit(20).all()
    logger.info(f"Admin {current_user.username} accessed dashboard")
    return render_template('admin/dashboard.html', stats=stats, recent_logs=recent_logs)


# ---------- CHALLENGE MANAGEMENT (Maker + Admin, no 2FA) ----------

@admin_bp.route('/challenges')
@login_required
@maker_required
def list_challenges():
    challenges = Challenge.query.all()
    return render_template('admin/challenges.html', challenges=challenges)


@admin_bp.route('/challenges/add', methods=['GET', 'POST'])
@login_required
@maker_required
def add_challenge():
    form = ChallengeForm()
    form.category_id.choices = [(c.id, c.name) for c in Category.query.order_by('name')]
    if form.validate_on_submit():
        chal = Challenge(
            category_id=form.category_id.data,
            title=form.title.data,
            description=form.description.data,
            difficulty=form.difficulty.data,
            points=form.points.data,
            flag=form.flag.data,
            is_active=form.is_active.data,
            type=form.type.data,
            file_url=form.file_url.data,
            challenge_url=form.challenge_url.data
        )
        db.session.add(chal)
        db.session.commit()
        log_msg = f"Added challenge '{chal.title}' (ID {chal.id})"
        logger.warning(f"Admin {current_user.username} {log_msg}")
        send_admin_alert("Challenge Added", f"User: {current_user.username}\nChallenge: {chal.title}\nCategory: {chal.category.name}\nType: {chal.type}\nPoints: {chal.points}\nFlag: {chal.flag}")
        log_admin_action("Challenge Added", f"Challenge: {chal.title} (ID {chal.id})")
        flash('Challenge added successfully!', 'success')
        return redirect(url_for('admin.list_challenges'))
    return render_template('admin/challenge_form.html', form=form, title='Add Challenge')


@admin_bp.route('/challenges/edit/<int:challenge_id>', methods=['GET', 'POST'])
@login_required
@maker_required
def edit_challenge(challenge_id):
    chal = Challenge.query.get_or_404(challenge_id)
    form = ChallengeForm(obj=chal)
    form.category_id.choices = [(c.id, c.name) for c in Category.query.order_by('name')]
    if form.validate_on_submit():
        old_title = chal.title
        chal.category_id = form.category_id.data
        chal.title = form.title.data
        chal.description = form.description.data
        chal.difficulty = form.difficulty.data
        chal.points = form.points.data
        chal.flag = form.flag.data
        chal.is_active = form.is_active.data
        chal.type = form.type.data
        chal.file_url = form.file_url.data
        chal.challenge_url = form.challenge_url.data
        db.session.commit()
        log_msg = f"Edited challenge '{chal.title}' (ID {chal.id})"
        logger.warning(f"Admin {current_user.username} {log_msg}")
        send_admin_alert("Challenge Edited", f"User: {current_user.username}\nChallenge: {old_title} → {chal.title}\nNew Points: {chal.points}\nNew Flag: {chal.flag}")
        log_admin_action("Challenge Edited", f"Challenge: {old_title} → {chal.title} (ID {chal.id})")
        flash('Challenge updated!', 'success')
        return redirect(url_for('admin.list_challenges'))
    return render_template('admin/challenge_form.html', form=form, title='Edit Challenge')


@admin_bp.route('/challenges/delete/<int:challenge_id>', methods=['POST'])
@login_required
@maker_required
def delete_challenge(challenge_id):
    chal = Challenge.query.get_or_404(challenge_id)
    title = chal.title
    db.session.delete(chal)
    db.session.commit()
    log_msg = f"Deleted challenge '{title}' (ID {challenge_id})"
    logger.warning(f"Admin {current_user.username} {log_msg}")
    send_admin_alert("Challenge Deleted", f"User: {current_user.username}\nChallenge: {title}\nID: {challenge_id}")
    log_admin_action("Challenge Deleted", f"Challenge: {title} (ID {challenge_id})")
    flash('Challenge deleted.', 'success')
    return redirect(url_for('admin.list_challenges'))


# ---------- CATEGORY MANAGEMENT (Admin only, 2FA required) ----------

@admin_bp.route('/categories')
@login_required
@admin_2fa_required
def list_categories():
    categories = Category.query.all()
    return render_template('admin/categories.html', categories=categories)


@admin_bp.route('/categories/add', methods=['GET', 'POST'])
@login_required
@admin_2fa_required
def add_category():
    form = CategoryForm()
    if form.validate_on_submit():
        cat = Category(name=form.name.data, description=form.description.data)
        db.session.add(cat)
        db.session.commit()
        log_msg = f"Added category '{cat.name}'"
        logger.warning(f"Admin {current_user.username} {log_msg}")
        send_admin_alert("Category Added", f"User: {current_user.username}\nCategory: {cat.name}\nDescription: {cat.description}")
        log_admin_action("Category Added", f"Category: {cat.name}")
        flash('Category created!', 'success')
        return redirect(url_for('admin.list_categories'))
    return render_template('admin/category_form.html', form=form, title='Add Category')


@admin_bp.route('/categories/edit/<int:category_id>', methods=['GET', 'POST'])
@login_required
@admin_2fa_required
def edit_category(category_id):
    cat = Category.query.get_or_404(category_id)
    form = CategoryForm(obj=cat)
    if form.validate_on_submit():
        old_name = cat.name
        cat.name = form.name.data
        cat.description = form.description.data
        db.session.commit()
        log_msg = f"Edited category '{old_name}' → '{cat.name}'"
        logger.warning(f"Admin {current_user.username} {log_msg}")
        send_admin_alert("Category Edited", f"User: {current_user.username}\nOld Name: {old_name}\nNew Name: {cat.name}")
        log_admin_action("Category Edited", f"Category: {old_name} → {cat.name}")
        flash('Category updated!', 'success')
        return redirect(url_for('admin.list_categories'))
    return render_template('admin/category_form.html', form=form, title='Edit Category')


@admin_bp.route('/categories/delete/<int:category_id>', methods=['POST'])
@login_required
@admin_2fa_required
def delete_category(category_id):
    cat = Category.query.get_or_404(category_id)
    if cat.challenges:
        flash('Cannot delete category with existing challenges. Remove or reassign them first.', 'danger')
        return redirect(url_for('admin.list_categories'))
    name = cat.name
    db.session.delete(cat)
    db.session.commit()
    log_msg = f"Deleted category '{name}'"
    logger.warning(f"Admin {current_user.username} {log_msg}")
    send_admin_alert("Category Deleted", f"User: {current_user.username}\nCategory: {name}")
    log_admin_action("Category Deleted", f"Category: {name}")
    flash('Category deleted.', 'success')
    return redirect(url_for('admin.list_categories'))


# ---------- USER MANAGEMENT (Admin only, 2FA required) ----------

@admin_bp.route('/users')
@login_required
@admin_2fa_required
def list_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)


@admin_bp.route('/users/toggle_admin/<int:user_id>', methods=['POST'])
@login_required
@admin_2fa_required
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot change your own role.', 'warning')
        return redirect(url_for('admin.list_users'))
    new_role = 'user' if user.role == 'admin' else 'admin'
    user.role = new_role
    db.session.commit()
    log_msg = f"{'Granted' if new_role == 'admin' else 'Revoked'} admin for {user.username}"
    logger.warning(f"Admin {current_user.username} {log_msg}")
    send_admin_alert("Role Changed", f"User: {current_user.username}\nTarget: {user.username}\nNew Role: {new_role}")
    log_admin_action("Role Changed", f"User: {user.username} → Role={new_role}")
    flash(f'Role for {user.username} updated to {new_role}.', 'success')
    return redirect(url_for('admin.list_users'))


@admin_bp.route('/users/update_xp/<int:user_id>', methods=['POST'])
@login_required
@admin_2fa_required
def update_user_xp(user_id):
    user = User.query.get_or_404(user_id)
    try:
        new_xp = int(request.form.get('xp', 0))
        if new_xp < 0:
            flash('XP cannot be negative.', 'danger')
            return redirect(url_for('admin.list_users'))
        old_xp = user.xp
        user.xp = new_xp
        db.session.commit()
        log_admin_action("User XP Updated", f"User: {user.username} (ID {user.id}), XP: {old_xp} → {new_xp}")
        flash(f'XP for {user.username} updated to {new_xp}.', 'success')
    except ValueError:
        flash('Invalid XP value. Please enter a number.', 'danger')
    return redirect(url_for('admin.list_users'))


@admin_bp.route('/users/update_rank/<int:user_id>', methods=['POST'])
@login_required
@admin_2fa_required
def update_user_rank(user_id):
    user = User.query.get_or_404(user_id)
    custom_rank = request.form.get('custom_rank', '').strip()
    user.custom_rank = custom_rank if custom_rank else None
    db.session.commit()
    log_admin_action("User Rank Updated", f"User: {user.username}, New rank: {custom_rank or 'XP-based'}")
    flash(f'Rank for {user.username} updated.', 'success')
    return redirect(url_for('admin.list_users'))

@admin_bp.route('/users/set_role/<int:user_id>', methods=['POST'])
@login_required
@admin_2fa_required
def set_user_role(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot change your own role.', 'warning')
        return redirect(url_for('admin.list_users'))
    new_role = request.form.get('role', 'user')
    if new_role not in ['admin', 'maker', 'user']:
        flash('Invalid role.', 'danger')
        return redirect(url_for('admin.list_users'))
    user.role = new_role
    db.session.commit()
    log_admin_action("Role Changed", f"User: {user.username} → Role={new_role}")
    flash(f'Role for {user.username} updated to {new_role}.', 'success')
    return redirect(url_for('admin.list_users'))

@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_2fa_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin.list_users'))
    username = user.username
    Solve.query.filter_by(user_id=user.id).delete()
    AdminLog.query.filter_by(admin_id=user.id).delete()
    db.session.delete(user)
    db.session.commit()
    log_admin_action("User Deleted", f"User: {username} (ID {user_id})")
    flash(f'User {username} has been deleted.', 'success')
    return redirect(url_for('admin.list_users'))


# ---------- SYSTEM SETTINGS (Admin only, 2FA required) ----------

@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_2fa_required
def system_settings():
    form = SystemSettingsForm()
    current_msg = Setting.get('system_log_message', 'Capture all flags to unlock S-Rank content.')
    if form.validate_on_submit():
        Setting.set('system_log_message', form.system_log_message.data)
        log_admin_action("System Settings Updated", f"New System Log: {form.system_log_message.data[:50]}...")
        flash('System log updated successfully!', 'success')
        return redirect(url_for('admin.system_settings'))
    form.system_log_message.data = current_msg
    return render_template('admin/settings.html', form=form)