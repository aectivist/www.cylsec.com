from app import create_app, db
from app.models import Category, User, Challenge, Setting
from werkzeug.security import generate_password_hash
from app.utils import generate_secure_password
import traceback
import sys

app = create_app()

with app.app_context():
    try:
        # Create tables if they don't exist
        db.create_all()
        print("[DEBUG] Tables created/checked", file=sys.stderr, flush=True)

        # --- Categories ---
        print("[DEBUG] Starting category seeding...", file=sys.stderr, flush=True)
        categories = ['Web', 'Crypto', 'Forensics', 'OSINT']
        cat_count = 0
        for cat_name in categories:
            if not Category.query.filter_by(name=cat_name).first():
                db.session.add(Category(name=cat_name))
                cat_count += 1
        db.session.commit()
        print(f"✅ {cat_count} categories seeded.")

        # --- Admin user ---
        print("[DEBUG] Checking for admin user...", file=sys.stderr, flush=True)
        admin_exists = User.query.filter_by(username='admin').first()
        print(f"[DEBUG] Admin exists: {admin_exists}", file=sys.stderr, flush=True)
        if not admin_exists:
            print("[DEBUG] Creating admin user...", file=sys.stderr, flush=True)
            admin_password = generate_secure_password(24)
            admin = User(
                username='admin',
                email='admin@cylsec.com',
                password_hash=generate_password_hash(admin_password),
                xp=0,
                role='admin',
                confirmed=True
            )
            print(f"[DEBUG] Admin object created: {admin}", file=sys.stderr, flush=True)
            db.session.add(admin)
            print("[DEBUG] Admin added to session", file=sys.stderr, flush=True)
            db.session.commit()
            print(f"✅ Admin user created (admin) -- generated password: {admin_password}")
        else:
            print(f"✅ Admin user already exists")

        # --- Maker user ---
        print("[DEBUG] Checking for maker user...", file=sys.stderr, flush=True)
        maker_exists = User.query.filter_by(username='maker').first()
        print(f"[DEBUG] Maker exists: {maker_exists}", file=sys.stderr, flush=True)
        if not maker_exists:
            print("[DEBUG] Creating maker user...", file=sys.stderr, flush=True)
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
            print(f"✅ Maker user created (maker) -- generated password: {maker_password}")
        else:
            print(f"✅ Maker user already exists")

        # --- Regular user (hunter) ---
        print("[DEBUG] Checking for hunter user...", file=sys.stderr, flush=True)
        hunter_exists = User.query.filter_by(username='hunter').first()
        print(f"[DEBUG] Hunter exists: {hunter_exists}", file=sys.stderr, flush=True)
        if not hunter_exists:
            print("[DEBUG] Creating hunter user...", file=sys.stderr, flush=True)
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
            print(f"✅ Hunter user created (hunter) -- generated password: {hunter_password}")
        else:
            print(f"✅ Hunter user already exists")

        print("\n🎉 Database seeding complete!")
    except Exception as e:
        print(f"\n❌ Seeding failed: {str(e)}", file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)