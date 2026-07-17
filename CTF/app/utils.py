from flask import current_app, render_template, url_for, session, request
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from app import mail
import re
import secrets
import random
import string
import json
from datetime import datetime
from urllib.parse import urlparse, urljoin


def generate_confirmation_token(email):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return s.dumps(email, salt='email-confirm')


def confirm_token(token, expiration=3600):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = s.loads(token, salt='email-confirm', max_age=expiration)
        return email
    except (BadSignature, SignatureExpired):
        return False


def _send_mail(msg):
    """Attempt to send mail. Silently logs and returns False on any failure."""
    try:
        if current_app.config.get('MAIL_SUPPRESS_SEND'):
            current_app.logger.info(f'[mail suppressed] to={msg.recipients} subject={msg.subject}')
            return True
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.warning(f'Mail send failed ({msg.subject}): {e}')
        return False


def send_confirmation_email(user_email, token):
    confirm_url = url_for('auth.confirm_email', token=token, _external=True)
    msg = Message(
        'Confirm Your Email – CYLVERN Security',
        sender=current_app.config.get('MAIL_DEFAULT_SENDER'),
        recipients=[user_email]
    )
    msg.body = f'Please confirm your email by visiting: {confirm_url}'
    msg.html = render_template('email/confirm.html', confirm_url=confirm_url)
    return _send_mail(msg)


def generate_reset_token(email):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return s.dumps(email, salt='password-reset')


def verify_reset_token(token, expiration=1800):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = s.loads(token, salt='password-reset', max_age=expiration)
        return email
    except (BadSignature, SignatureExpired):
        return False


def send_password_reset_email(user_email, token):
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    msg = Message(
        'Reset Your Password – CYLVERN Security',
        sender=current_app.config.get('MAIL_DEFAULT_SENDER'),
        recipients=[user_email]
    )
    msg.body = f'Reset your password at: {reset_url}'
    msg.html = render_template('email/reset.html', reset_url=reset_url)
    return _send_mail(msg)


def generate_registration_token(email):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return s.dumps(email, salt='registration-confirm')


def verify_registration_token(token, expiration=86400):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = s.loads(token, salt='registration-confirm', max_age=expiration)
        return email
    except (BadSignature, SignatureExpired):
        return False


def send_registration_confirmation_email(user_email, token):
    confirm_url = url_for('auth.confirm_registration', token=token, _external=True)
    msg = Message(
        'Complete Your Registration – CYLVERN Security',
        sender=current_app.config.get('MAIL_DEFAULT_SENDER'),
        recipients=[user_email]
    )
    msg.body = f'Complete your registration at: {confirm_url}'
    msg.html = render_template('email/confirm_registration.html', confirm_url=confirm_url)
    return _send_mail(msg)


def generate_otp():
    return str(random.randint(100000, 999999))


def send_otp_email(user_email, otp):
    msg = Message(
        'Your OTP – CYLVERN Security',
        sender=current_app.config.get('MAIL_DEFAULT_SENDER'),
        recipients=[user_email]
    )
    msg.body = f'Your one-time password is: {otp}'
    msg.html = render_template('email/otp.html', otp=otp)
    return _send_mail(msg)


def is_strong_password(password):
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'\d', password):
        return False
    return True


def generate_secure_password(length=16):
    alphabet = string.ascii_letters + string.digits + '-_'
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc
