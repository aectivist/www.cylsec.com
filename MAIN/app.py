import os
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
from wtforms import StringField, PasswordField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, Optional
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# ── Security config ──────────────────────────────────────────────────────────
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL') or 'sqlite:///cylvern_main.db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = (
    os.environ.get('SESSION_COOKIE_SECURE', 'true').lower() in ('true', '1')
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

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)


class Alert(db.Model):
    __tablename__ = 'alerts'
    id         = db.Column(db.Integer, primary_key=True)
    message    = db.Column(db.String(500), nullable=False, default='')
    is_active  = db.Column(db.Boolean, default=False)
    level      = db.Column(db.String(20), default='info')   # info | warning | danger
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Inquiry(db.Model):
    """Stores business / public-sector contact form submissions."""
    __tablename__ = 'inquiries'
    id           = db.Column(db.Integer, primary_key=True)
    name         = db.Column(db.String(120), nullable=False)
    org          = db.Column(db.String(120), nullable=True)
    email        = db.Column(db.String(120), nullable=False)
    inquiry_type = db.Column(db.String(50), nullable=False)   # pentest | security | other
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


class AlertForm(FlaskForm):
    message   = StringField('Alert Message', validators=[Length(max=500)])
    is_active = BooleanField('Show alert to all visitors')
    level     = StringField('Level (info / warning / danger)', validators=[DataRequired()])
    submit    = SubmitField('Save Alert')


class InquiryForm(FlaskForm):
    name         = StringField('Full Name',     validators=[DataRequired(), Length(max=120)])
    org          = StringField('Organisation',  validators=[Optional(), Length(max=120)])
    email        = StringField('Email Address', validators=[DataRequired(), Email(), Length(max=120)])
    inquiry_type = StringField('Inquiry Type',  validators=[DataRequired()])
    message      = TextAreaField('Message',     validators=[DataRequired(), Length(min=20, max=3000)])
    submit       = SubmitField('Send Inquiry')

# ── DB init helper ────────────────────────────────────────────────────────────
def init_db():
    with app.app_context():
        db.create_all()
        # Seed default admin if none exists
        if not AdminUser.query.first():
            admin = AdminUser(username=os.environ.get('ADMIN_USERNAME', 'admin'))
            admin.set_password(os.environ.get('ADMIN_PASSWORD', 'changeme123!'))
            db.session.add(admin)
            db.session.commit()
        # Seed single alert row if none exists
        if not Alert.query.first():
            db.session.add(Alert(message='', is_active=False, level='info'))
            db.session.commit()

# ── Context processor: inject alert into every template ───────────────────────
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
            org=form.org.data.strip() if form.org.data else None,
            email=form.email.data.strip().lower(),
            inquiry_type=form.inquiry_type.data,
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

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin_panel():
    alert = Alert.query.first()
    form  = AlertForm(obj=alert)
    if form.validate_on_submit():
        level = form.level.data.strip().lower()
        if level not in ('info', 'warning', 'danger'):
            level = 'info'
        alert.message   = form.message.data.strip()
        alert.is_active = form.is_active.data
        alert.level     = level
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
