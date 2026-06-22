from flask import Blueprint, render_template
from flask_login import current_user
from app.models import Category, User, Challenge, Setting
from sqlalchemy.sql.expression import func

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    categories = Category.query.all()
    leaderboard = User.query.order_by(User.xp.desc()).limit(10).all()
    progress = 0
    if current_user.is_authenticated:
        progress = (current_user.xp % 1000) / 10

    random_challenges = Challenge.query.filter_by(is_active=True).order_by(func.random()).limit(6).all()
    system_log_msg = Setting.get('system_log_message', 'Capture all flags to unlock S-Rank content.')

    return render_template('index.html',
                           categories=categories,
                           leaderboard=leaderboard,
                           progress=progress,
                           random_challenges=random_challenges,
                           setting_system_log=system_log_msg)

@main_bp.route('/leaderboard')
def leaderboard():
    top = User.query.order_by(User.xp.desc()).limit(10).all()
    return render_template('leaderboard.html', top=top)