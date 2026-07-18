# CYLVERN CTF Platform

Flask-based Capture The Flag platform running at **ctf.cylsec.com**.  
Handles user registration/login, challenges, flag submission, a Docker instance manager for live challenge containers, and an admin panel.

---

## Stack

| Layer | Technology |
|---|---|
| App | Python 3.11 · Flask 3.0 · SQLAlchemy 2.0 |
| Auth | Flask-Login · Flask-WTF (CSRF) · pyotp (TOTP 2FA) |
| Mail | Flask-Mail → Zoho SMTP |
| Rate limiting | Flask-Limiter (in-memory or Redis) |
| DB | SQLite (dev) · PostgreSQL (docker-compose) |
| Migrations | Flask-Migrate (Alembic) |
| Docker instances | docker SDK · APScheduler (cleanup every 5 min) |
| Process manager | gunicorn (1 worker) via systemd |
| Reverse proxy | Nginx → 127.0.0.1:5000 |

---

## Directory layout

```
CTF/
├── app/
│   ├── __init__.py          # App factory, extensions, error handlers
│   ├── models.py            # User, Challenge, Category, Solve, DockerInstance, …
│   ├── forms.py             # Login, Register, ForgotPassword, ResetPassword
│   ├── admin_forms.py       # ChallengeForm, CategoryForm, SystemSettingsForm
│   ├── utils.py             # Token helpers, mail senders, OTP
│   ├── docker_manager.py    # Spawn / stop / extend Docker containers
│   ├── instance_manager.py  # Enumerate available cylvern/* images
│   ├── scheduler.py         # APScheduler cleanup task
│   ├── blueprints/
│   │   ├── auth.py          # /auth/* — login, register, reset, 2FA
│   │   ├── challenges.py    # /challenges/* — archive, submit flag
│   │   ├── docker.py        # /docker/* — launch, extend, stop instances
│   │   ├── admin.py         # /admin/* — dashboard, CRUD, user management
│   │   └── main.py          # / — index, leaderboard, profile
│   ├── templates/
│   └── static/
├── CTF_Instances/
│   └── Web_Instances/
│       └── xss-ashal/       # Example Docker challenge (Flask + SQLite)
├── migrations/              # Alembic migration history
├── config.py                # Config class (reads from .env)
├── run.py                   # Development entrypoint
├── seed.py                  # Seeds categories, admin, maker, hunter users
├── entrypoint.sh            # Production startup (db init → gunicorn)
├── cylvern-ctf.service      # systemd unit
├── nginx-ctf.conf           # Nginx server block
├── docker-compose.yml       # Optional Docker Compose (web + postgres)
├── Dockerfile               # Container image definition
└── requirements.txt
```

---

## First-time setup (bare-metal VPS)

```bash
cd /root/www.cylsec.com/CTF

# 1. Create and activate venv
python3.11 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env (see Environment variables section below)
cp .env.example .env
nano .env

# 4. Run migrations and seed default users
flask db upgrade
python seed.py

# 5. Install and start the systemd service
cp cylvern-ctf.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now cylvern-ctf

# 6. Install Nginx config
cp nginx-ctf.conf /etc/nginx/sites-available/ctf.cylsec.com
ln -sf /etc/nginx/sites-available/ctf.cylsec.com /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

# 7. Get SSL cert
certbot --nginx -d ctf.cylsec.com
```

---

## Environment variables (`.env`)

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | **Yes** | 32-byte hex secret — generate with `python3 -c 'import secrets; print(secrets.token_hex(32))'` |
| `DATABASE_URL` | No | Postgres URL e.g. `postgresql://user:pass@localhost/db`. Defaults to SQLite. |
| `MAIL_SERVER` | No | SMTP host. Defaults to `smtp.zoho.com` |
| `MAIL_PORT` | No | SMTP port. Defaults to `587` |
| `MAIL_USE_TLS` | No | `true` / `false`. Defaults to `true` |
| `MAIL_USERNAME` | No | SMTP login. If unset, mail is suppressed and registration auto-confirms. |
| `MAIL_PASSWORD` | No | SMTP password / app password |
| `MAIL_DEFAULT_SENDER` | No | From address. Defaults to `MAIL_USERNAME` |
| `ADMIN_ALERT_EMAIL` | No | Where 500-error alerts go. Defaults to `MAIL_USERNAME` |
| `SESSION_COOKIE_SECURE` | No | Set `true` once HTTPS is live |
| `REMEMBER_COOKIE_SECURE` | No | Set `true` once HTTPS is live |
| `INSTANCE_HOST` | No | Public hostname for Docker instance URLs. Defaults to `localhost` — **must be set to your domain/IP in production** |
| `PORT_RANGE_START` | No | First port for Docker instances. Defaults to `10000` |
| `PORT_RANGE_END` | No | Last port for Docker instances. Defaults to `11000` |
| `REDIS_LINK` | No | Redis URI for rate-limiter shared storage e.g. `redis://127.0.0.1:6379/0`. Defaults to in-memory. |

---

## Docker challenge instances

Challenge containers are spawned on demand per user. Each gets a random port in the configured range and is publicly accessible at `http://<INSTANCE_HOST>:<port>`.

**Requirements:**
- Docker daemon running on the host
- Challenge images built and tagged as `cylvern/<image-name>` (e.g. `cylvern/xss-ashal`)
- Ports `10000–11000` open in firewall and cloud security group

**Building a challenge image:**
```bash
cd CTF_Instances/Web_Instances/xss-ashal
docker build -t cylvern/xss-ashal .
```

Expired instances are cleaned up automatically every 5 minutes by APScheduler.

---

## Admin panel

`https://ctf.cylsec.com/admin` — login with an account that has `role = admin`.

Default credentials seeded by `seed.py` are printed to stdout on first run. **Change them immediately.**

---

## Updating on the VPS

```bash
cd /root/www.cylsec.com && git pull origin main
systemctl restart cylvern-ctf
```
