from app import db
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy import func
import pyotp 

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    xp = db.Column(db.Integer, default=0)
    role = db.Column(db.String(20), default='user')  # 'admin', 'maker', 'user'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    confirmed = db.Column(db.Boolean, default=False)
    confirmed_at = db.Column(db.DateTime, nullable=True)
    custom_rank = db.Column(db.String(50), nullable=True)
    rank_color = db.Column(db.String(7), nullable=True)
    two_factor_enabled = db.Column(db.Boolean, default=False)
    totp_secret = db.Column(db.String(32), nullable=True)  # Base32 secret for TOTP

    solves = db.relationship('Solve', backref='user', lazy=True)

    @property
    def is_admin(self):
        return self.role == 'admin'

    def get_rank(self):
        if self.custom_rank:
            return self.custom_rank
        if self.xp >= 20000:
            return 'S+ Mythic'
        elif self.xp >= 10000:
            return 'S-Rank Hero'
        elif self.xp >= 5000:
            return 'A-Rank Hunter'
        elif self.xp >= 1000:
            return 'B-Rank Defender'
        elif self.xp >= 500:
            return 'C-Rank Savant'
        else:
            return 'E-Rank Novice'

    def get_totp_uri(self):
        """Generate the TOTP URI for QR code."""
        if not self.totp_secret:
            return None
        return pyotp.totp.TOTP(self.totp_secret).provisioning_uri(
            name=self.email,
            issuer_name="CYLVERN Security"
        )
    @classmethod
    def get_by_username_insensitive(cls, username):
        return cls.query.filter(func.lower(cls.username) == func.lower(username)).first()

    @classmethod
    def is_username_taken(cls, username, exclude_id=None):
        query = cls.query.filter(func.lower(cls.username) == func.lower(username))
        if exclude_id:
            query = query.filter(cls.id != exclude_id)
        return query.first() is not None


class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    icon = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)
    challenges = db.relationship('Challenge', backref='category', lazy=True)


class Challenge(db.Model):
    __tablename__ = 'challenges'
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    difficulty = db.Column(db.String(20), default='Medium')
    points = db.Column(db.Integer, default=100)
    flag = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    # Modular fields
    type = db.Column(db.String(20), default='web')
    file_url = db.Column(db.String(200), nullable=True)
    challenge_url = db.Column(db.String(200), nullable=True)


class Solve(db.Model):
    __tablename__ = 'solves'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenges.id'), nullable=False)
    solved_at = db.Column(db.DateTime, default=datetime.utcnow)

    challenge = db.relationship('Challenge', backref='solves')


class AdminLog(db.Model):
    __tablename__ = 'admin_logs'
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(200), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('admin_logs', cascade='all, delete-orphan'), lazy=True)


class Setting(db.Model):
    __tablename__ = 'settings'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)

    @classmethod
    def get(cls, key, default=None):
        setting = cls.query.filter_by(key=key).first()
        return setting.value if setting else default

    @classmethod
    def set(cls, key, value):
        setting = cls.query.filter_by(key=key).first()
        if setting:
            setting.value = value
        else:
            setting = cls(key=key, value=value)
            db.session.add(setting)
        db.session.commit()