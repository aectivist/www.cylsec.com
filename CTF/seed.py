from app import db
from app.models import User, Category, Challenge, Setting
from werkzeug.security import generate_password_hash
from app.utils import generate_secure_password
import traceback
import sys
from app import create_app

app = create_app()

with app.app_context():
    try:
        db.create_all()
        print("[DEBUG] Tables created/checked", file=sys.stderr, flush=True)

        categories = ['Web', 'Crypto', 'Forensics', 'OSINT']
        cat_count = 0
        for cat_name in categories:
            if not Category.query.filter_by(name=cat_name).first():
                db.session.add(Category(name=cat_name))
                cat_count += 1
        db.session.commit()
        print(f"[+] {cat_count} categories seeded.")

        admin_exists = User.query.filter_by(username='admin').first()
        if not admin_exists:
            admin_password = generate_secure_password(24)
            admin = User(
                username='admin',
                email='admin@cylsec.com',
                password_hash=generate_password_hash(admin_password),
                xp=0,
                role='admin',
                confirmed=True
            )
            db.session.add(admin)
            db.session.commit()
            print(f"[+] Admin user created -- password: {admin_password}")
        else:
            print(f"[+] Admin user already exists")

        maker_exists = User.query.filter_by(username='maker').first()
        if not maker_exists:
            maker_password = generate_secure_password(20)
            maker = User(
                username='maker',
                email='maker@cylvern.com',
                password_hash=generate_password_hash(maker_password),
                xp=0,
                role='maker',
                confirmed=True
            )
            db.session.add(maker)
            db.session.commit()
            print(f"[+] Maker user created -- password: {maker_password}")
        else:
            print(f"[+] Maker user already exists")

        hunter_exists = User.query.filter_by(username='hunter').first()
        if not hunter_exists:
            hunter_password = generate_secure_password(16)
            hunter = User(
                username='hunter',
                email='hunter@cylsec.com',
                password_hash=generate_password_hash(hunter_password),
                xp=350,
                role='user',
                confirmed=True
            )
            db.session.add(hunter)
            db.session.commit()
            print(f"[+] Hunter user created -- password: {hunter_password}")
        else:
            print(f"[+] Hunter user already exists")

        print("\n[+] Database seeding complete!")
    except Exception as e:
        print(f"\n[-] Seeding failed: {str(e)}", file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)
