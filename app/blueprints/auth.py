from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, session
from flask_login import login_required, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy import func
from app import db, limiter
from app.models import User
from app.forms import LoginForm, RegistrationForm
from app.utils import (
    generate_registration_token,
    verify_registration_token,
    send_registration_confirmation_email,
    confirm_token,
    send_password_reset_email,
    verify_reset_token,
    generate_otp,
    send_otp_email
)
import pyotp

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter(func.lower(User.username) == func.lower(form.username.data)).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            if not user.confirmed:
                flash('Please confirm your email address before logging in. Check your inbox for the confirmation link.', 'warning')
                return render_template('login.html', form=form)
            # Check if TOTP is enabled
            if user.totp_secret:
                # Store user id temporarily and redirect to 2FA verification
                session['pending_2fa_user_id'] = user.id
                session['pending_2fa_redirect'] = request.args.get('next') or url_for('main.index')
                return redirect(url_for('auth.two_factor_login_verification'))
            # No 2FA, log in directly
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.index'))
        flash('Invalid username or password.', 'danger')
    return render_template('login.html', form=form)


@auth_bp.route('/verify-2fa-login', methods=['GET', 'POST'])
def two_factor_login_verification():
    # Check if there's a pending user
    user_id = session.get('pending_2fa_user_id')
    if not user_id:
        flash('No pending 2FA verification.', 'danger')
        return redirect(url_for('auth.login'))
    user = User.query.get(user_id)
    if not user:
        session.pop('pending_2fa_user_id', None)
        flash('User not found.', 'danger')
        return redirect(url_for('auth.login'))
    if request.method == 'POST':
        code = request.form.get('code', '').strip()
        if not code:
            flash('Please enter the 6‑digit code.', 'danger')
            return render_template('auth/verify_2fa_login.html')
        totp = pyotp.TOTP(user.totp_secret)
        if totp.verify(code):
            # Code is correct – log the user in
            login_user(user)
            session.pop('pending_2fa_user_id', None)
            session.pop('pending_2fa_redirect', None)
            session['2fa_verified'] = True  # Mark as verified for this session
            next_page = session.get('pending_2fa_redirect') or url_for('main.index')
            return redirect(next_page)
        else:
            flash('Invalid code. Please try again.', 'danger')
    return render_template('auth/verify_2fa_login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("3 per minute")
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check case‑insensitive username and email
        if User.query.filter(func.lower(User.username) == func.lower(form.username.data)).first():
            flash('Username already taken.', 'danger')
            return render_template('register.html', form=form)
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered.', 'danger')
            return render_template('register.html', form=form)

        # Prepare data for token
        user_data = {
            'username': form.username.data,
            'email': form.email.data,
            'password_hash': generate_password_hash(form.password.data)
        }
        token = generate_registration_token(user_data)
        send_registration_confirmation_email(user_data['email'], token, user_data['username'])
        flash('A confirmation email has been sent to your address. Please click the link to complete registration.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html', form=form)


@auth_bp.route('/confirm-registration/<token>')
def confirm_registration(token):
    data = verify_registration_token(token)
    if not data:
        flash('The confirmation link is invalid or has expired. Please register again.', 'danger')
        return redirect(url_for('auth.register'))
    # Re-check that the username/email are still available (race condition)
    if User.query.filter(func.lower(User.username) == func.lower(data['username'])).first():
        flash('Username is already taken. Please register with a different username.', 'danger')
        return redirect(url_for('auth.register'))
    if User.query.filter_by(email=data['email']).first():
        flash('Email is already registered. Please use a different email.', 'danger')
        return redirect(url_for('auth.register'))
    # Create user
    user = User(
        username=data['username'],
        email=data['email'],
        password_hash=data['password_hash'],
        confirmed=True,
        confirmed_at=datetime.utcnow()
    )
    db.session.add(user)
    db.session.commit()
    flash('Your account has been confirmed! You can now log in.', 'success')
    return redirect(url_for('auth.login'))


# Keep the old /confirm/<token> route for backward compatibility (optional)
@auth_bp.route('/confirm/<token>')
def confirm_email(token):
    email = confirm_token(token)
    if not email:
        flash('The confirmation link is invalid or has expired.', 'danger')
        return redirect(url_for('auth.login'))
    user = User.query.filter_by(email=email).first_or_404()
    if user.confirmed:
        flash('Account already confirmed. Please log in.', 'info')
    else:
        user.confirmed = True
        user.confirmed_at = datetime.utcnow()
        db.session.commit()
        flash('Your account has been confirmed! You can now log in.', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
@limiter.limit("3 per minute")
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            send_password_reset_email(user)
            flash('A password reset link has been sent to your email.', 'success')
        else:
            flash('No account found with that email address.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    return render_template('auth/forgot_password.html')


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    email = verify_reset_token(token)
    if not email:
        flash('The reset link is invalid or has expired.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    if request.method == 'POST':
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')
        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/reset_password.html', token=token)
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('User not found.', 'danger')
            return redirect(url_for('auth.forgot_password'))
        user.password_hash = generate_password_hash(password)
        db.session.commit()
        flash('Your password has been updated! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', token=token)


# ---------- OTP Routes ----------
@auth_bp.route('/send-otp', methods=['POST'])
@login_required
def send_otp():
    purpose = request.form.get('purpose')
    if purpose not in ['email_change', 'account_delete', 'admin_2fa']:
        flash('Invalid purpose.', 'danger')
        return redirect(url_for('main.index'))
    otp = generate_otp()
    session['otp_code'] = otp
    session['otp_purpose'] = purpose
    session['otp_timestamp'] = datetime.utcnow().timestamp()
    send_otp_email(current_user, purpose, otp)
    flash('OTP sent to your email.', 'success')
    return render_template('auth/verify_otp.html', purpose=purpose)


@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
@login_required
def verify_otp():
    if request.method == 'POST':
        code = request.form.get('code')
        stored_code = session.get('otp_code')
        purpose = session.get('otp_purpose')
        timestamp = session.get('otp_timestamp')
        if not stored_code or not timestamp:
            flash('No OTP request found.', 'danger')
            return redirect(url_for('main.index'))
        if (datetime.utcnow().timestamp() - timestamp) > 300:  # 5 min
            flash('OTP expired. Please request a new one.', 'danger')
            session.pop('otp_code', None)
            session.pop('otp_purpose', None)
            session.pop('otp_timestamp', None)
            return redirect(url_for('main.index'))
        if code == stored_code:
            session['otp_verified'] = True
            session.pop('otp_code', None)
            session.pop('otp_timestamp', None)
            flash('OTP verified.', 'success')
            if purpose == 'email_change':
                return redirect(url_for('auth.change_email'))
            elif purpose == 'account_delete':
                return redirect(url_for('auth.delete_account'))
            elif purpose == 'admin_2fa':
                return redirect(url_for('admin.verify_2fa_confirm'))
            else:
                return redirect(url_for('main.index'))
        else:
            flash('Invalid OTP.', 'danger')
    return render_template('auth/verify_otp.html', purpose=session.get('otp_purpose'))


@auth_bp.route('/change-email', methods=['GET', 'POST'])
@login_required
def change_email():
    if not session.get('otp_verified'):
        flash('Please verify OTP first.', 'warning')
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        new_email = request.form.get('new_email', '').strip()
        if not new_email or '@' not in new_email:
            flash('Please enter a valid email address.', 'danger')
            return render_template('auth/change_email.html')
        if User.query.filter_by(email=new_email).first():
            flash('Email already registered.', 'danger')
            return render_template('auth/change_email.html')
        old_email = current_user.email
        current_user.email = new_email
        db.session.commit()
        session.pop('otp_verified', None)
        session.pop('otp_purpose', None)
        flash(f'Email updated from {old_email} to {new_email}.', 'success')
        return redirect(url_for('main.index'))
    return render_template('auth/change_email.html')


@auth_bp.route('/delete-account', methods=['GET', 'POST'])
@login_required
def delete_account():
    if not session.get('otp_verified'):
        flash('Please verify OTP first.', 'warning')
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        password = request.form.get('password')
        if not check_password_hash(current_user.password_hash, password):
            flash('Incorrect password.', 'danger')
            return render_template('auth/delete_account.html')
        db.session.delete(current_user)
        db.session.commit()
        session.clear()
        flash('Your account has been deleted.', 'info')
        return redirect(url_for('main.index'))
    return render_template('auth/delete_account.html')


# Keep the inline username update (optional)
@auth_bp.route('/update_username', methods=['POST'])
@login_required
@limiter.limit("5 per minute")
def update_username():
    new_username = request.form.get('new_username', '').strip()
    if not new_username or len(new_username) < 3:
        flash('Username must be at least 3 characters.', 'danger')
        return redirect(url_for('main.index'))
    existing = User.query.filter(
        func.lower(User.username) == func.lower(new_username),
        User.id != current_user.id
    ).first()
    if existing:
        flash('Username already taken.', 'danger')
        return redirect(url_for('main.index'))
    current_user.username = new_username
    db.session.commit()
    flash('Username updated successfully!', 'success')
    return redirect(url_for('main.index'))


@auth_bp.route('/send-password-reset', methods=['POST'])
@login_required
def send_password_reset():
    send_password_reset_email(current_user)
    flash('A password reset link has been sent to your email. Follow the link to set a new password.', 'success')
    return redirect(url_for('main.index'))