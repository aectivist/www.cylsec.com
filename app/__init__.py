from flask import Flask, render_template, request, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail, Message
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import Config
import random
import traceback
from datetime import datetime
import os
<<<<<<< HEAD
=======
from dotenv import load_dotenv

load_dotenv()
>>>>>>> cde75ce499f633f714bacaa69f5e4a118840f2ca

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()
mail = Mail()

login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

limiter = Limiter(
    get_remote_address,
    default_limits=["200 per day", "50 per hour"],
<<<<<<< HEAD
    storage_uri=os.environ.get('REDIS_LINK', 'memory://')  # fallback added
)

=======
    storage_uri=os.environ.get('REDIS_LINK')   # or "memory://" for development
)


>>>>>>> cde75ce499f633f714bacaa69f5e4a118840f2ca
def create_app(config_class=Config):
    app = Flask(__name__, template_folder='templates')
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
<<<<<<< HEAD
        from app.models import User
        return User.query.get(int(user_id))

=======
        from app.models import User   # import inside to avoid circular import
        return User.query.get(int(user_id))

    # Register blueprints
>>>>>>> cde75ce499f633f714bacaa69f5e4a118840f2ca
    from app.blueprints.main import main_bp
    from app.blueprints.auth import auth_bp
    from app.blueprints.challenges import challenges_bp
    from app.blueprints.admin import admin_bp
<<<<<<< HEAD
    from app.blueprints.dungeon import dungeon_bp
=======
>>>>>>> cde75ce499f633f714bacaa69f5e4a118840f2ca

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(challenges_bp, url_prefix='/challenges')
    app.register_blueprint(admin_bp, url_prefix='/admin')
<<<<<<< HEAD
    app.register_blueprint(dungeon_bp)

=======

    # Context processor
>>>>>>> cde75ce499f633f714bacaa69f5e4a118840f2ca
    @app.context_processor
    def inject_subtitle():
        subtitles = [
            "Do you have what it takes?",
            "Ascend Through Cybersecurity. Hack the Future. Earn Glory.",
            "Try harder!",
            "The system awaits.",
            "Are you prepared?",
            "Capture flags, earn glory.",
            "Train like a hunter.",
            "Become the ultimate Hunter."
        ]
        return {'subtitle': random.choice(subtitles)}

<<<<<<< HEAD
=======
    # -------- Error Handlers ----------
>>>>>>> cde75ce499f633f714bacaa69f5e4a118840f2ca
    @app.errorhandler(400)
    def bad_request(e):
        return render_template('errors/400.html'), 400

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(429)
    def ratelimit_handler(e):
        return render_template('errors/429.html'), 429

    @app.errorhandler(500)
    def internal_server_error(e):
        app.logger.error(f"500 error: {e}")
<<<<<<< HEAD
        try:
            from app.models import User
=======

        # Send email to all admins
        try:
            from app.models import User   # import inside to avoid circular import
>>>>>>> cde75ce499f633f714bacaa69f5e4a118840f2ca
            admins = User.query.filter_by(role='admin').all()
            if admins:
                subject = "[CYLVERN] Server Error (500)"
                body = f"""
Server Error occurred at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

URL: {request.url}
Method: {request.method}
IP: {request.remote_addr}
User-Agent: {request.headers.get('User-Agent')}

Error: {e}

Traceback:
{''.join(traceback.format_tb(e.__traceback__)) if e.__traceback__ else 'No traceback available'}
                """
                msg = Message(
                    subject=subject,
                    sender=app.config.get('MAIL_USERNAME'),
                    recipients=[admin.email for admin in admins]
                )
                msg.body = body
                mail.send(msg)
        except Exception as mail_error:
            app.logger.error(f"Failed to send admin alert email: {mail_error}")
<<<<<<< HEAD
        return render_template('errors/500.html'), 500

=======

        return render_template('errors/500.html'), 500


>>>>>>> cde75ce499f633f714bacaa69f5e4a118840f2ca
    return app