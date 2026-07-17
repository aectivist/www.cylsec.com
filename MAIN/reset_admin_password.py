"""
Run once to reset the admin password:
  python reset_admin_password.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from app import app, db, AdminUser
from dotenv import load_dotenv

load_dotenv()

NEW_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'changeme123')

with app.app_context():
    admin = AdminUser.query.first()
    if not admin:
        admin = AdminUser(username=os.environ.get('ADMIN_USERNAME', 'admin'))
        db.session.add(admin)
    admin.set_password(NEW_PASSWORD)
    db.session.commit()
    print(f"Password reset for user '{admin.username}' → '{NEW_PASSWORD}'")
