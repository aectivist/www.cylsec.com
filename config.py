import os
import secrets
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Require an explicit SECRET_KEY in production. For development, generate
    # a temporary secure key so sessions aren't trivially guessable.
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        if os.environ.get('FLASK_ENV') == 'production' or os.environ.get('ENV') == 'production':
            raise RuntimeError('SECRET_KEY must be set in the environment for production deployments')
        SECRET_KEY = secrets.token_hex(32)

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///cylvern.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Cookie / session security defaults (can be overridden by env vars)
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'true').lower() in ['true', '1', 'yes']
    SESSION_COOKIE_HTTPONLY = os.environ.get('SESSION_COOKIE_HTTPONLY', 'true').lower() in ['true', '1', 'yes']
    REMEMBER_COOKIE_SECURE = os.environ.get('REMEMBER_COOKIE_SECURE', 'true').lower() in ['true', '1', 'yes']
    REMEMBER_COOKIE_HTTPONLY = os.environ.get('REMEMBER_COOKIE_HTTPONLY', 'true').lower() in ['true', '1', 'yes']
    SESSION_COOKIE_SAMESITE = os.environ.get('SESSION_COOKIE_SAMESITE', 'Lax')

    # Zoho Mail SMTP
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.zoho.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMIN_ALERT_EMAIL = os.environ.get('ADMIN_ALERT_EMAIL') or MAIL_USERNAME