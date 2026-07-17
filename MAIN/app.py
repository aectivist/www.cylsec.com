import os
import io
import base64
import secrets
from datetime import datetime
from flask import (Flask, render_template, redirect, url_for,
                   request, flash, session, abort)
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from flask_login import (LoginManager, UserMixin,
                         login_user, logout_user,
                         login_required, current_user)
from wtforms import StringField, PasswordField, TextAreaField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, Email, Optional
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import pyotp
import qrcode

load_dotenv()

app = Flask(__name__)

# ── Security config ───────────────────────────────────────────────────────────
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL') or 'sqlite:///cylvern_main.db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = (
    os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() in ('true', '1')
)
app.config['WTF_CSRF_TIME_LIMIT'] = 3600

db = SQLAlchemy(app)
csrf = CSRFProtect(app)
login_manager = LoginManager(app)
login_manager.login_view = 'admin_login'
login_manager.login_message_category = 'danger'

# ── Security headers ──────────────────────────────────────────────────────────
@app.after_request
def set_headers(response):
    response.headers.setdefault('X-Frame-Options', 'SAMEORIGIN')
    response.headers.setdefault('X-Content-Type-Options', 'nosniff')
    response.headers.setdefault('X-XSS-Protection', '1; mode=block')
    response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
    response.headers.setdefault(
        'Permissions-Policy',
        'geolocation=(), microphone=(), camera=()'
    )
    return response

# ── Models ────────────────────────────────────────────────────────────────────
class AdminUser(UserMixin, db.Model):
    __tablename__ = 'admin_users'
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    totp_secret   = db.Column(db.String(64), nullable=True)
    totp_enabled  = db.Column(db.Boolean, default=False, nullable=False)

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)

    def get_totp_uri(self):
        return pyotp.TOTP(self.totp_secret).provisioning_uri(
            name=self.username, issuer_name='Cylvern Security'
        )

    def verify_totp(self, code):
        return pyotp.TOTP(self.totp_secret).verify(code, valid_window=1)


class Alert(db.Model):
    __tablename__ = 'alerts'
    id         = db.Column(db.Integer, primary_key=True)
    message    = db.Column(db.String(500), nullable=False, default='')
    is_active  = db.Column(db.Boolean, default=False)
    level      = db.Column(db.String(20), default='info')   # info | warning | danger
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Inquiry(db.Model):
    __tablename__ = 'inquiries'
    id           = db.Column(db.Integer, primary_key=True)
    name         = db.Column(db.String(120), nullable=False)
    org          = db.Column(db.String(120), nullable=True)
    email        = db.Column(db.String(120), nullable=False)
    inquiry_type = db.Column(db.String(50), nullable=True)
    message      = db.Column(db.Text, nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    read         = db.Column(db.Boolean, default=False)


@login_manager.user_loader
def load_user(user_id):
    return AdminUser.query.get(int(user_id))

# ── Forms ─────────────────────────────────────────────────────────────────────
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(max=80)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit   = SubmitField('Sign In')


class TotpForm(FlaskForm):
    code = StringField('Authenticator Code', validators=[DataRequired(), Length(min=6, max=6)])


class TotpSetupForm(FlaskForm):
    code = StringField('Verify Code', validators=[DataRequired(), Length(min=6, max=6)])


class AlertForm(FlaskForm):
    message   = StringField('Alert Message', validators=[Length(max=500)])
    is_active = BooleanField('Show alert to all visitors')
    level     = StringField('Level (info / warning / danger)', validators=[DataRequired()])
    submit    = SubmitField('Save Alert')


class InquiryForm(FlaskForm):
    name    = StringField('Full Name',            validators=[DataRequired(), Length(max=120)])
    email   = StringField('Email Address',        validators=[DataRequired(), Email(), Length(max=120)])
    company = StringField('Company / Organisation', validators=[Optional(), Length(max=120)])
    service = SelectField('Service of Interest',  choices=[
        ('', '— Select a service —'),
        ('pentest',    'Penetration Testing'),
        ('vuln-assess','Vulnerability Assessment'),
        ('red-team',   'Red Team Exercise'),
        ('incident',   'Incident Response'),
        ('compliance', 'Security Compliance'),
        ('training',   'Security Training'),
        ('other',      'Other / General Enquiry'),
    ])
    message = TextAreaField('Message',            validators=[DataRequired(), Length(min=20, max=3000)])
    submit  = SubmitField('Send Enquiry')

# ── DB migration + seed ───────────────────────────────────────────────────────
def _migrate_db():
    """Apply incremental schema changes that db.create_all() won't handle."""
    migrations = [
        "ALTER TABLE admin_users ADD COLUMN totp_secret TEXT",
        "ALTER TABLE admin_users ADD COLUMN totp_enabled INTEGER NOT NULL DEFAULT 0",
    ]
    with db.engine.connect() as conn:
        for sql in migrations:
            try:
                conn.execute(db.text(sql))
                conn.commit()
            except Exception:
                pass  # column already exists


def init_db():
    with app.app_context():
        db.create_all()
        _migrate_db()
        # Seed default admin if none exists
        if not AdminUser.query.first():
            admin = AdminUser(username=os.environ.get('ADMIN_USERNAME', 'admin'))
            admin.set_password(os.environ.get('ADMIN_PASSWORD', 'changeme123'))
            db.session.add(admin)
            db.session.commit()
        # Seed single alert row if none exists
        if not Alert.query.first():
            db.session.add(Alert(message='', is_active=False, level='info'))
            db.session.commit()

# ── Context processor ─────────────────────────────────────────────────────────
@app.context_processor
def inject_alert():
    alert = Alert.query.first()
    return {'site_alert': alert}

# ── Public routes ─────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/individuals')
def individuals():
    return render_template('individuals.html')

@app.route('/individuals/ctf')
def ctf_page():
    return render_template('wip.html', page_name='CTF Platform')

@app.route('/individuals/academy')
def academy_page():
    return render_template('wip.html', page_name='Academy')

@app.route('/individuals/mentorship')
def mentorship_page():
    return render_template('wip.html', page_name='Private Mentorship')

@app.route('/vdp')
def vdp():
    return render_template('vdp.html')

@app.route('/business', methods=['GET', 'POST'])
def business():
    form = InquiryForm()
    success = False
    if form.validate_on_submit():
        inq = Inquiry(
            name=form.name.data.strip(),
            org=form.company.data.strip() if form.company.data else None,
            email=form.email.data.strip().lower(),
            inquiry_type=form.service.data or '',
            message=form.message.data.strip(),
        )
        db.session.add(inq)
        db.session.commit()
        success = True
    return render_template('business.html', form=form, success=success)

# ── Admin routes ──────────────────────────────────────────────────────────────
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_panel'))
    form = LoginForm()
    if form.validate_on_submit():
        user = AdminUser.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            if user.totp_enabled:
                session['_2fa_user_id'] = user.id
                return redirect(url_for('admin_2fa_verify'))
            login_user(user)
            return redirect(url_for('admin_panel'))
        flash('Invalid credentials.', 'danger')
    return render_template('admin/login.html', form=form)


@app.route('/admin/logout', methods=['POST'])
@login_required
def admin_logout():
    logout_user()
    flash('Signed out.', 'info')
    return redirect(url_for('admin_login'))


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


@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin_panel():
    alert = Alert.query.first()
    form  = AlertForm(obj=alert)
    if form.validate_on_submit():
        level = form.level.data.strip().lower()
        if level not in ('info', 'warning', 'danger'):
            level = 'info'
        alert.message    = form.message.data.strip()
        alert.is_active  = form.is_active.data
        alert.level      = level
        alert.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Alert updated.', 'success')
        return redirect(url_for('admin_panel'))
    inquiries = Inquiry.query.order_by(Inquiry.submitted_at.desc()).limit(50).all()
    return render_template('admin/panel.html', form=form, inquiries=inquiries, alert=alert)


@app.route('/admin/inquiry/<int:inquiry_id>/read', methods=['POST'])
@login_required
def mark_read(inquiry_id):
    inq = Inquiry.query.get_or_404(inquiry_id)
    inq.read = True
    db.session.commit()
    return redirect(url_for('admin_panel'))


# ── Error pages ───────────────────────────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403

@app.errorhandler(500)
def server_error(e):
    return render_template('errors/500.html'), 500

if __name__ == '__main__':
    init_db()
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(debug=debug, host='127.0.0.1', port=5001)
