from app import create_app, db
from app.models import Category, User, Challenge
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    db.create_all()

    # Categories
    categories = ['Web', 'Pwn', 'Crypto', 'Forensics', 'OSINT', 'Reverse Engineering']
    for cat_name in categories:
        if not Category.query.filter_by(name=cat_name).first():
            db.session.add(Category(name=cat_name))
    db.session.commit()

    # Admin user
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            email='admin@cylsec.com',
            password_hash=generate_password_hash('admin123!'),
            xp=0,
            role='admin',
            confirmed=True
        )
        db.session.add(admin)

    # Maker user
    if not User.query.filter_by(username='maker').first():
        maker = User(
            username='maker',
            email='maker@cylsec.com',
            password_hash=generate_password_hash('MakerPass1!'),
            xp=0,
            role='maker',
            confirmed=True
        )
        db.session.add(maker)

    # Regular user (hunter)
    if not User.query.filter_by(username='hunter').first():
        hunter = User(
            username='hunter',
            email='hunter@cylvern.com',
            password_hash=generate_password_hash('password'),
            xp=350,
            role='user',
            confirmed=True
        )
        db.session.add(hunter)

    # Default system log message
    from app.models import Setting
    if not Setting.get('system_log_message'):
        Setting.set('system_log_message', 'Capture all flags to unlock S-Rank content.')

    db.session.commit()
    print("✅ Database seeded successfully!")