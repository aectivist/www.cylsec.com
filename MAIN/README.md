# CYLVERN Security — Main Site

Flask marketing/company site running at **cylsec.com** and **www.cylsec.com**.  
Serves the public landing pages, business enquiry form, and a single-user admin panel for managing site alerts and reading enquiries.

---

## Stack

| Layer | Technology |
|---|---|
| App | Python 3.11 · Flask 2.2 |
| Auth | Flask-Login · Flask-WTF (CSRF) · pyotp (TOTP 2FA) |
| DB | SQLite (`instance/cylvern_main.db`) |
| Process manager | gunicorn (2 workers) via systemd |
| Reverse proxy | Nginx → 127.0.0.1:5001 |

---

## Directory layout

```
MAIN/
├── app.py                  # Entire application (models, routes, forms in one file)
├── run.py                  # Development entrypoint (runs on 127.0.0.1:5001)
├── reset_admin_password.py # One-shot script to reset the admin password
├── entrypoint.sh           # Production startup script
├── cylvern-main.service    # systemd unit
├── nginx-cylsec.conf       # Nginx server block for cylsec.com
├── requirements.txt
├── instance/
│   └── cylvern_main.db     # SQLite database (git-ignored)
├── static/                 # CSS, JS, images
└── templates/
    ├── base.html
    ├── index.html           # Landing page
    ├── individuals.html     # Individuals services page
    ├── business.html        # Business enquiry page + form
    ├── vdp.html             # Vulnerability Disclosure Policy
    ├── wip.html             # "Coming soon" placeholder
    ├── admin/               # Admin panel templates
    └── errors/              # 403, 404, 500
```

---

## First-time setup (bare-metal VPS)

```bash
cd /root/www.cylsec.com/MAIN

# 1. Create and activate venv
python3.11 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env (see Environment variables below)
nano .env

# 4. Install and start the systemd service
cp cylvern-main.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now cylvern-main

# 5. Install Nginx config
cp nginx-cylsec.conf /etc/nginx/sites-available/cylsec.com
ln -sf /etc/nginx/sites-available/cylsec.com /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

# 6. Get SSL cert
certbot --nginx -d cylsec.com -d www.cylsec.com
```

The database and default admin user are created automatically on first request.  
Default credentials: `admin` / `changeme123` — **change immediately** via the admin panel or `reset_admin_password.py`.

---

## Environment variables (`.env`)

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | Recommended | Flask secret key. Auto-generates a random one per process if unset — **set a stable value in production** or sessions won't survive restarts |
| `DATABASE_URL` | No | Defaults to `sqlite:///cylvern_main.db` |
| `SESSION_COOKIE_SECURE` | No | Set `true` once HTTPS is live |
| `ADMIN_USERNAME` | No | Username for the seeded admin account. Defaults to `admin` |
| `ADMIN_PASSWORD` | No | Password for the seeded admin account. Defaults to `changeme123` |

---

## Admin panel

`https://cylsec.com/admin` — single-user admin protected by password + optional TOTP 2FA.

**Features:**
- Set a sitewide alert banner (info / warning / danger) shown to all visitors
- View and mark-as-read business enquiries submitted via the contact form
- Enable / disable TOTP two-factor authentication

---

## Resetting the admin password

```bash
cd /root/www.cylsec.com/MAIN
source venv/bin/activate
ADMIN_PASSWORD=yournewpassword python reset_admin_password.py
```

---

## Updating on the VPS

```bash
cd /root/www.cylsec.com && git pull origin main
systemctl restart cylvern-main
```
