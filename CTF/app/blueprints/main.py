from flask import Blueprint, render_template, abort
from flask_login import current_user, login_required
from app.models import Category, User, Challenge, Solve

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    categories = Category.query.all()
    top_users = User.query.order_by(User.xp.desc()).limit(3).all()
    # 5 most recently added active challenges across all categories
    recent_challenges = (Challenge.query
                         .filter_by(is_active=True)
                         .order_by(Challenge.id.desc())
                         .limit(5).all())
    return render_template('index.html',
                           categories=categories,
                           top_users=top_users,
                           recent_challenges=recent_challenges)


@main_bp.route('/leaderboard')
def leaderboard():
    users = User.query.order_by(User.xp.desc()).all()
    return render_template('leaderboard.html', users=users)


@main_bp.route('/profile')
@login_required
def profile():
    solved_ids = {s.challenge_id for s in current_user.solves}
    solved_challenges = (Challenge.query
                         .filter(Challenge.id.in_(solved_ids))
                         .all() if solved_ids else [])
    return render_template('profile.html',
                           user=current_user,
                           solved_challenges=solved_challenges)
