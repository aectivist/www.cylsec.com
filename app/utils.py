from flask import current_app, render_template, url_for
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer
from app import mail

def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='email-confirm-salt')

def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt='email-confirm-salt',
            max_age=expiration
        )
    except:
        return None
    return email

def send_confirmation_email(user):
    token = generate_confirmation_token(user.email)
    confirm_url = url_for('auth.confirm_email', token=token, _external=True)
    html = render_template('email/confirm.html', user=user, confirm_url=confirm_url)
    subject = "Please confirm your CYLVERN Security account"
    msg = Message(subject,
                  sender=current_app.config['MAIL_USERNAME'],
                  recipients=[user.email])
    msg.html = html
    mail.send(msg)
def generate_reset_token(email):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='password-reset-salt')

def verify_reset_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt='password-reset-salt',
            max_age=expiration
        )
    except:
        return None
    return email

def send_password_reset_email(user):
    token = generate_reset_token(user.email)
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    html = render_template('email/reset.html', user=user, reset_url=reset_url)
    subject = "Reset your CYLVERN Security password"
    msg = Message(subject,
                  sender=current_app.config['MAIL_USERNAME'],
                  recipients=[user.email])
    msg.html = html
    mail.send(msg)

import json
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

def generate_registration_token(data):
    """Generate a token containing registration data (username, email, password_hash)."""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    # data is a dict; we serialize to JSON
    return serializer.dumps(json.dumps(data), salt='registration-salt')

def verify_registration_token(token, expiration=3600):
    """Verify token and return the registration data dict, or None if invalid."""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        payload = serializer.loads(token, salt='registration-salt', max_age=expiration)
        return json.loads(payload)  # convert back to dict
    except (BadSignature, SignatureExpired, json.JSONDecodeError):
        return None
    
def send_registration_confirmation_email(email, token, username):
    confirm_url = url_for('auth.confirm_registration', token=token, _external=True)
    html = render_template('email/confirm_registration.html', username=username, confirm_url=confirm_url)
    subject = "Complete your CYLVERN Security registration"
    msg = Message(subject, sender=current_app.config['MAIL_USERNAME'], recipients=[email])
    msg.html = html
    mail.send(msg)

import random
import string
from flask import current_app, session
from flask_mail import Message
from app import mail
from datetime import datetime

def generate_otp():
    """Generate a 6‑digit numeric OTP."""
    return ''.join(random.choices(string.digits, k=6))

def send_otp_email(user, purpose, otp):
    """Send OTP via email with purpose."""
    html = render_template('email/otp.html', user=user, otp=otp, purpose=purpose)
    subject = f"CYLVERN Security - {purpose} OTP"
    msg = Message(subject, sender=current_app.config['MAIL_USERNAME'], recipients=[user.email])
    msg.html = html
    mail.send(msg)

# Also ensure you have the other token functions for registration, etc.