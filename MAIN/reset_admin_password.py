"""
Run once to reset the MAIN admin password to 'changeme123'.
Usage: python reset_admin_password.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app import app, db, AdminUser

with app.app_context():
    admin = AdminUser.query.filter_by(username='admin').first()
    if not admin:
        admin = AdminUser(username='admin')
        db.session.add(admin)
    admin.set_password('changeme123')
    admin.totp_enabled = False
    db.session.commit()
    print("✓ Admin password reset to: changeme123")
