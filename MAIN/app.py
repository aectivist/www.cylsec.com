import os
import io
import base64
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, request, flash, abort, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import (LoginManager, UserMixin, login_user, logout_user,
                         login_required, current_user)
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import StringField, PasswordField, TextAreaField, BooleanField, SelectField
from wtforms.validators import DataRequired, Email, Length, Optional
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import pyotp
import qrcode

load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()


# ─── Models ───────────────────────────────────────────────────────────────────

class AdminUser(UserMixin, db.Model):
    __tablename__ = 'admin_users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    totp_secret = db.Column(db.String(64), nullable=True)
    totp_enabled = db.Column(db.Boolean, default=False, nullable=False)

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)

    def get_totp_uri(self):
        return pyotp.totp.TOTP(self.totp_secret).provisioning_uri(
            name=self.username, issuer_name='Cylvern Security'
        )

    def verify_totp(self, code):
        return pyotp.TOTP(self.totp_secret).verify(code, valid_window=1)


class Alert(db.Model):
    __tablename__ = 'alerts'
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(512), nullable=False)
    level = db.Column(db.String(20), default='info')   # info | warning | danger | success
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Inquiry(db.Model):
    __tablename__ = 'inquiries'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(254), nullable=False)
    company = db.Column(db.String(120))
    message = db.Column(db.Text, nullable=False)
    service = db.Column(db.String(80))
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)


# ─── Forms ────────────────────────────────────────────────────────────────────

class AdminLoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(max=80)])
    password = PasswordField('Password', validators=[DataRequired()])


class TotpForm(FlaskForm):
    code = StringField('Authenticator Code', validators=[DataRequired(), Length(min=6, max=6)])


class TotpSetupForm(FlaskForm):
    code = StringField('Verify Code', validators=[DataRequired(), Length(min=6, max=6)])


class AlertForm(FlaskForm):
    message = StringField('Message', validators=[DataRequired(), Length(max=512)])
    level = SelectField('Level', choices=[
        ('info', 'Info'), ('warning', 'Warning'),
        ('danger', 'Danger'), ('success', 'Success')
    ])
    active = BooleanField('Active', default=True)


class InquiryForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=120)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=254)])
    company = StringField('Company / Organisation', validators=[Optional(), Length(max=120)])
    service = SelectField('Service of Interest', choices=[
        ('', '— Select a service —'),
        ('pentest', 'Penetration Testing'),
        ('vuln-assess', 'Vulnerability Assessment'),
        ('red-team', 'Red Team Exercise'),
        ('incident', 'Incident Response'),
        ('compliance', 'Security Compliance'),
        ('training', 'Security Training'),
        ('other', 'Other / General Enquiry'),
    ], validators=[Optional()])
    message = TextAreaField('Message', validators=[DataRequired(), Length(max=4000)])


# ─── App factory ──────────────────────────────────────────────────────────────

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'change-me-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(app.instance_path, 'cylvern_main.db')
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['WTF_CSRF_ENABLED'] = True

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = 'admin_login'
    login_manager.login_message = 'Please log in to access the admin panel.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        return AdminUser.query.get(int(user_id))

    # Security headers on every response
    @app.after_request
    def security_headers(response):
        response.headers.setdefault('X-Frame-Options', 'SAMEORIGIN')
        response.headers.setdefault('X-Content-Type-Options', 'nosniff')
        response.headers.setdefault('X-XSS-Protection', '1; mode=block')
        response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
        response.headers.setdefault(
            'Content-Security-Policy',
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com "
            "https://cdnjs.cloudflare.com; "
            "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com data:; "
            "img-src 'self' data:;"
        )
        return response

    # Context processor — inject active alerts and current datetime into every template
    @app.context_processor
    def inject_globals():
        try:
            active_alerts = Alert.query.filter_by(active=True).order_by(Alert.created_at.desc()).all()
        except Exception:
            active_alerts = []
        return {'active_alerts': active_alerts, 'now': datetime.utcnow()}

    with app.app_context():
        db.create_all()
        _seed_admin()

    # ── Public routes ──────────────────────────────────────────────────────────

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/individuals')
    def individuals():
        return render_template('individuals.html')

    @app.route('/business', methods=['GET', 'POST'])
    def business():
        form = InquiryForm()
        if form.validate_on_submit():
            inq = Inquiry(
                name=form.name.data,
                email=form.email.data,
                company=form.company.data or '',
                service=form.service.data or '',
                message=form.message.data,
            )
            db.session.add(inq)
            db.session.commit()
            flash('Your enquiry has been received. We will be in touch shortly.', 'success')
            return redirect(url_for('business'))
        return render_template('business.html', form=form)

    @app.route('/vdp')
    def vdp():
        return render_template('vdp.html')

    @app.route('/wip')
    def wip():
        return render_template('wip.html')

    # ── Admin routes ───────────────────────────────────────────────────────────

    @app.route('/admin/login', methods=['GET', 'POST'])
    def admin_login():
        if current_user.is_authenticated:
            return redirect(url_for('admin_panel'))
        form = AdminLoginForm()
        if form.validate_on_submit():
            user = AdminUser.query.filter_by(username=form.username.data).first()
            if user and user.check_password(form.password.data):
                if user.totp_enabled:
                    # Store user id in session, redirect to 2FA step
                    session['_2fa_user_id'] = user.id
                    return redirect(url_for('admin_2fa_verify'))
                login_user(user)
                return redirect(url_for('admin_panel'))
            flash('Invalid credentials.', 'danger')
        return render_template('admin/login.html', form=form)

    @app.route('/admin/2fa/verify', methods=['GET', 'POST'])
    def admin_2fa_verify():
        user_id = session.get('_2fa_user_id')
        if not user_id:
            return redirect(url_for('admin_login'))
        user = AdminUser.query.get(user_id)
        if not user:
            session.pop('_2fa_user_id', None)
            return redirect(url_for('admin_login'))
        form = TotpForm()
        if form.validate_on_submit():
            if user.verify_totp(form.code.data):
                session.pop('_2fa_user_id', None)
                login_user(user)
                return redirect(url_for('admin_panel'))
            flash('Invalid authenticator code.', 'danger')
        return render_template('admin/2fa_verify.html', form=form)

    @app.route('/admin/2fa/setup', methods=['GET', 'POST'])
    @login_required
    def admin_2fa_setup():
        user = current_user
        form = TotpSetupForm()

        # Generate a new secret if the user doesn't have one yet
        if not user.totp_secret:
            user.totp_secret = pyotp.random_base32()
            db.session.commit()

        if form.validate_on_submit():
            if user.verify_totp(form.code.data):
                user.totp_enabled = True
                db.session.commit()
                flash('Two-factor authentication enabled.', 'success')
                return redirect(url_for('admin_panel'))
            flash('Code incorrect — please try again.', 'danger')

        # Build QR code as inline data URI
        qr_img = qrcode.make(user.get_totp_uri())
        buf = io.BytesIO()
        qr_img.save(buf, format='PNG')
        qr_b64 = base64.b64encode(buf.getvalue()).decode()

        return render_template('admin/2fa_setup.html', form=form,
                               qr_b64=qr_b64, secret=user.totp_secret)

    @app.route('/admin/2fa/disable', methods=['POST'])
    @login_required
    def admin_2fa_disable():
        current_user.totp_enabled = False
        current_user.totp_secret = None
        db.session.commit()
        flash('Two-factor authentication disabled.', 'warning')
        return redirect(url_for('admin_panel'))

    @app.route('/admin/logout')
    @login_required
    def admin_logout():
        logout_user()
        return redirect(url_for('index'))

    @app.route('/admin', methods=['GET', 'POST'])
    @login_required
    def admin_panel():
        alert_form = AlertForm()
        if alert_form.validate_on_submit() and request.form.get('action') == 'create_alert':
            a = Alert(
                message=alert_form.message.data,
                level=alert_form.level.data,
                active=alert_form.active.data,
            )
            db.session.add(a)
            db.session.commit()
            flash('Alert created.', 'success')
            return redirect(url_for('admin_panel'))

        alerts = Alert.query.order_by(Alert.created_at.desc()).all()
        inquiries = Inquiry.query.order_by(Inquiry.submitted_at.desc()).all()
        return render_template('admin/panel.html',
                               alert_form=alert_form,
                               alerts=alerts,
                               inquiries=inquiries)

    @app.route('/admin/alert/<int:alert_id>/toggle', methods=['POST'])
    @login_required
    def toggle_alert(alert_id):
        a = Alert.query.get_or_404(alert_id)
        a.active = not a.active
        db.session.commit()
        flash(f'Alert {"activated" if a.active else "deactivated"}.', 'success')
        return redirect(url_for('admin_panel'))

    @app.route('/admin/alert/<int:alert_id>/delete', methods=['POST'])
    @login_required
    def delete_alert(alert_id):
        a = Alert.query.get_or_404(alert_id)
        db.session.delete(a)
        db.session.commit()
        flash('Alert deleted.', 'success')
        return redirect(url_for('admin_panel'))

    @app.route('/admin/inquiry/<int:inquiry_id>/read', methods=['POST'])
    @login_required
    def mark_inquiry_read(inquiry_id):
        inq = Inquiry.query.get_or_404(inquiry_id)
        inq.read = True
        db.session.commit()
        return redirect(url_for('admin_panel'))

    @app.route('/admin/inquiry/<int:inquiry_id>/delete', methods=['POST'])
    @login_required
    def delete_inquiry(inquiry_id):
        inq = Inquiry.query.get_or_404(inquiry_id)
        db.session.delete(inq)
        db.session.commit()
        flash('Inquiry deleted.', 'success')
        return redirect(url_for('admin_panel'))

    # ── Error handlers ─────────────────────────────────────────────────────────

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('errors/500.html'), 500

    return app


def _seed_admin():
    """Create default admin account if none exists."""
    if AdminUser.query.count() == 0:
        admin = AdminUser(username='admin')
        admin.set_password(os.environ.get('ADMIN_PASSWORD', 'changeme123'))
        db.session.add(admin)
        db.session.commit()
