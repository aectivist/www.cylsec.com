from app import create_app, db
<<<<<<< HEAD
from app.models import Category, User, Challenge
=======
from app.models import Category, User, Challenge, Setting
>>>>>>> cde75ce499f633f714bacaa69f5e4a118840f2ca
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    db.create_all()

    # Categories
<<<<<<< HEAD
    categories = ['Web', 'Pwn', 'Crypto', 'Forensics', 'OSINT', 'Reverse Engineering']
=======
    categories = ['Web', 'Crypto', 'Forensics', 'OSINT']
>>>>>>> cde75ce499f633f714bacaa69f5e4a118840f2ca
    for cat_name in categories:
        if not Category.query.filter_by(name=cat_name).first():
            db.session.add(Category(name=cat_name))
    db.session.commit()

    # Admin user
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
<<<<<<< HEAD
            email='admin@cylsec.com',
            password_hash=generate_password_hash('admin123!'),
=======
            email='admin@cylvern.com',
            password_hash=generate_password_hash('admin123'),
>>>>>>> cde75ce499f633f714bacaa69f5e4a118840f2ca
            xp=0,
            role='admin',
            confirmed=True
        )
        db.session.add(admin)

    # Maker user
    if not User.query.filter_by(username='maker').first():
        maker = User(
            username='maker',
<<<<<<< HEAD
            email='maker@cylsec.com',
            password_hash=generate_password_hash('MakerPass1!'),
=======
            email='maker@cylvern.com',
            password_hash=generate_password_hash('maker123'),
>>>>>>> cde75ce499f633f714bacaa69f5e4a118840f2ca
            xp=0,
            role='maker',
            confirmed=True
        )
        db.session.add(maker)

<<<<<<< HEAD
    # Regular user (hunter)
=======
    # Regular user
>>>>>>> cde75ce499f633f714bacaa69f5e4a118840f2ca
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
<<<<<<< HEAD
    from app.models import Setting
=======
>>>>>>> cde75ce499f633f714bacaa69f5e4a118840f2ca
    if not Setting.get('system_log_message'):
        Setting.set('system_log_message', 'Capture all flags to unlock S-Rank content.')

    db.session.commit()
<<<<<<< HEAD
    print("✅ Database seeded successfully!")
=======
    print("✅ Database seeded with roles: admin (admin/admin123), maker (maker/maker123), hunter (hunter/password).")
>>>>>>> cde75ce499f633f714bacaa69f5e4a118840f2ca
