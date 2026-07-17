from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, session
from flask_login import login_required, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy import func
from app import db, limiter
from app.models import User
from app.forms import LoginForm, RegistrationForm, ForgotPasswordForm, ResetPasswordForm
from app.utils import (
    generate_registration_token, verify_registration_token,
    send_registration_confirmation_email, confirm_token,
    send_password_reset_email, verify_reset_token,
    generate_otp, send_otp_email, is_safe_url,
    generate_reset_token
)

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter(
            func.lower(User.username) == func.lower(form.username.data)
        ).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            if not user.confirmed:
                flash('Please confirm your email before logging in.', 'warning')
                return render_template('login.html', form=form)
            if user.two_factor_enabled:
                session['2fa_user_id'] = user.id
                return redirect(url_for('auth.verify_2fa_login'))
            login_user(user)
            next_page = request.args.get('next')
            if next_page and is_safe_url(next_page):
                return redirect(next_page)
            return redirect(url_for('main.index'))
        flash('Invalid username or password.', 'danger')
    return render_template('login.html', form=form)


@auth_bp.route('/verify-2fa-login', methods=['GET', 'POST'])
def verify_2fa_login():
    user_id = session.get('2fa_user_id')
    if not user_id:
        return redirect(url_for('auth.login'))
    user = User.query.get(user_id)
    if not user:
        return redirect(url_for('auth.login'))
    if request.method == 'POST':
        import pyotp
        token = request.form.get('token', '').strip()
        totp = pyotp.TOTP(user.totp_secret)
        if totp.verify(token):
            session.pop('2fa_user_id', None)
            login_user(user)
            return redirect(url_for('main.index'))
        flash('Invalid 2FA code.', 'danger')
    return render_template('auth/verify_2fa_login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("3 per minute")
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        if User.is_username_taken(form.username.data):
            flash('Username already taken.', 'danger')
            return render_template('register.html', form=form)
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered.', 'danger')
            return render_template('register.html', form=form)
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data),
            confirmed=False
        )
        db.session.add(user)
        db.session.commit()
        try:
            token = generate_registration_token(user.email)
            send_registration_confirmation_email(user.email, token)
            flash('Registration successful! Check your email to confirm your account.', 'success')
        except Exception:
            user.confirmed = True
            db.session.commit()
            flash('Registration successful! (Email confirmation unavailable — you may log in directly.)', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html', form=form)


@auth_bp.route('/confirm-registration/<token>')
def confirm_registration(token):
    email = verify_registration_token(token)
    if not email:
        flash('Invalid or expired confirmation link.', 'danger')
        return redirect(url_for('auth.login'))
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('auth.login'))
    if user.confirmed:
        flash('Account already confirmed.', 'info')
    else:
        user.confirmed = True
        user.confirmed_at = datetime.utcnow()
        db.session.commit()
        flash('Email confirmed! You may now log in.', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/confirm/<token>')
def confirm_email(token):
    email = confirm_token(token)
    if not email:
        flash('Invalid or expired confirmation link.', 'danger')
        return redirect(url_for('auth.login'))
    user = User.query.filter_by(email=email).first()
    if user and not user.confirmed:
        user.confirmed = True
        user.confirmed_at = datetime.utcnow()
        db.session.commit()
        flash('Email confirmed!', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            try:
                token = generate_reset_token(user.email)
                send_password_reset_email(user.email, token)
            except Exception:
                pass
        flash('If that email exists, a reset link has been sent.', 'info')
        return redirect(url_for('auth.login'))
    return render_template('auth/forgot_password.html', form=form)


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    email = verify_reset_token(token)
    if not email:
        flash('Invalid or expired reset link.', 'danger')
        return redirect(url_for('auth.login'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=email).first()
        if user:
            user.password_hash = generate_password_hash(form.password.data)
            db.session.commit()
            flash('Password reset successfully.', 'success')
            return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)


@auth_bp.route('/send-otp', methods=['POST'])
@login_required
def send_otp():
    otp = generate_otp()
    session['otp'] = otp
    session['otp_expiry'] = (datetime.utcnow().timestamp() + 300)
    try:
        send_otp_email(current_user.email, otp)
        flash('OTP sent to your email.', 'info')
    except Exception:
        flash('Failed to send OTP.', 'danger')
    return redirect(url_for('main.index'))


@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
@login_required
def verify_otp():
    if request.method == 'POST':
        entered = request.form.get('otp', '').strip()
        stored = session.get('otp')
        expiry = session.get('otp_expiry', 0)
        if stored and entered == stored and datetime.utcnow().timestamp() < expiry:
            session.pop('otp', None)
            session.pop('otp_expiry', None)
            flash('OTP verified.', 'success')
            return redirect(url_for('main.index'))
        flash('Invalid or expired OTP.', 'danger')
    return render_template('auth/verify_otp.html')


@auth_bp.route('/change-email', methods=['GET', 'POST'])
@login_required
def change_email():
    if request.method == 'POST':
        new_email = request.form.get('email', '').strip()
        if not new_email:
            flash('Email cannot be empty.', 'danger')
        elif User.query.filter_by(email=new_email).first():
            flash('Email already in use.', 'danger')
        else:
            current_user.email = new_email
            db.session.commit()
            flash('Email updated.', 'success')
            return redirect(url_for('main.index'))
    return render_template('auth/change_email.html')


@auth_bp.route('/delete-account', methods=['GET', 'POST'])
@login_required
def delete_account():
    if request.method == 'POST':
        password = request.form.get('password', '')
        if check_password_hash(current_user.password_hash, password):
            user = current_user._get_current_object()
            logout_user()
            db.session.delete(user)
            db.session.commit()
            flash('Account deleted.', 'info')
            return redirect(url_for('main.index'))
        flash('Incorrect password.', 'danger')
    return render_template('auth/delete_account.html')


@auth_bp.route('/update_username', methods=['POST'])
@login_required
def update_username():
    new_username = request.form.get('new_username', '').strip()
    if not new_username:
        flash('Username cannot be empty.', 'danger')
    elif User.is_username_taken(new_username, exclude_id=current_user.id):
        flash('Username already taken.', 'danger')
    else:
        current_user.username = new_username
        db.session.commit()
        flash('Username updated.', 'success')
    return redirect(url_for('main.index'))


@auth_bp.route('/send-password-reset', methods=['POST'])
@login_required
def send_password_reset():
    try:
        token = generate_reset_token(current_user.email)
        send_password_reset_email(current_user.email, token)
        flash('Password reset link sent to your email.', 'info')
    except Exception:
        flash('Failed to send reset email.', 'danger')
    return redirect(url_for('main.index'))
