from app import create_app, db
from app.models import Category, User, Challenge, Setting
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # Create tables if they don't exist
    db.create_all()

    # --- Categories ---
    categories = ['Web', 'Crypto', 'Forensics', 'OSINT']
    for cat_name in categories:
        if not Category.query.filter_by(name=cat_name).first():
            db.session.add(Category(name=cat_name))
    db.session.commit()
    print("✅ Categories seeded.")

    # --- Admin user ---
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            email='admin@cylsec.com',
            password_hash=generate_password_hash('admin1231!'),
            xp=0,
            role='admin',
            confirmed=True
        )
        db.session.add(admin)
        print("✅ Admin user created (admin / admin123).")

    # --- Maker user ---
    if not User.query.filter_by(username='maker').first():
        maker = User(
            username='maker',
            email='maker@cylvern.com',
            password_hash=generate_password_hash('maker1231!'),
            xp=0,
            role='maker',
            confirmed=True
        )
        db.session.add(maker)
        print("✅ Maker user created (maker / maker123).")

    # --- Regular user (hunter) ---
    if not User.query.filter_by(username='hunter').first():
        hunter = User(
            username='hunter',
            email='hunter@cylsec.com',
            password_hash=generate_password_hash('password1!'),
            xp=350,
            role='user',
            confirmed=True
        )
        db.session.add(hunter)
        print("✅ Hunter user created (hunter / password).")

    # --- Default system log message ---
    if not Setting.get('system_log_message'):
        Setting.set('system_log_message', 'Capture all flags to unlock S-Rank content.')
        print("✅ System log message set.")

    db.session.commit()
    print("\n🎉 Database seeding complete!")