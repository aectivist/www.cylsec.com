from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user
from app.models import Category, User, Challenge
from sqlalchemy.sql.expression import func

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    categories = Category.query.all()
    top_users = User.query.order_by(User.xp.desc()).limit(10).all()
    return render_template('index.html', categories=categories, top_users=top_users)


@main_bp.route('/leaderboard')
def leaderboard():
    users = User.query.order_by(User.xp.desc()).all()
    return render_template('leaderboard.html', users=users)
