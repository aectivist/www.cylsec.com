from flask import Blueprint, render_template, abort, flash, redirect, url_for, request
from flask_login import login_required, current_user
from app import db, limiter
from app.models import Category, Challenge, Solve

challenges_bp = Blueprint('challenges', __name__)

@challenges_bp.route('/archives')
@login_required
def archives():
    categories = Category.query.all()
    return render_template('archives.html', categories=categories)

@challenges_bp.route('/archives/<int:category_id>')
@login_required
def category_detail(category_id):   # <-- ADDED category_id parameter
    category = Category.query.get_or_404(category_id)
    challenges = Challenge.query.filter_by(category_id=category_id, is_active=True).all()
    return render_template('category.html', category=category, challenges=challenges)

@challenges_bp.route('/challenge/<int:challenge_id>')
@login_required
def view_challenge(challenge_id):   # <-- ADDED challenge_id parameter
    chal = Challenge.query.get_or_404(challenge_id)
    return render_template('challenge_detail.html', chal=chal)

@challenges_bp.route('/challenge/<int:challenge_id>/submit', methods=['POST'])
@login_required
@limiter.limit("10 per minute")
def submit_flag(challenge_id):     # <-- ADDED challenge_id parameter
    chal = Challenge.query.get_or_404(challenge_id)
    user_flag = request.form.get('flag', '').strip()
    if user_flag == chal.flag:
        solve = Solve.query.filter_by(user_id=current_user.id, challenge_id=chal.id).first()
        if not solve:
            solve = Solve(user_id=current_user.id, challenge_id=chal.id)
            db.session.add(solve)
            current_user.xp += chal.points
            db.session.commit()
            flash(f'✅ Flag correct! You earned {chal.points} XP!', 'success')
        else:
            flash('You already solved this challenge.', 'info')
    else:
        flash('❌ Incorrect flag. Try again.', 'danger')
    return redirect(url_for('challenges.view_challenge', challenge_id=chal.id))