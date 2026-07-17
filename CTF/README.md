# CYLVERN — Cybersecurity Learning Platform

A web-based CTF platform where authenticated users can solve challenges, launch isolated Docker instances, and earn XP.

## Tech Stack

- **Backend**: Flask 2.2 (Python 3.11)
- **Database**: PostgreSQL via SQLAlchemy + Alembic
- **Frontend**: HTML / CSS / JavaScript (Tailwind + custom)
- **Deployment**: Docker & Docker Compose
- **Instance system**: Docker-in-Docker via mounted socket (`/var/run/docker.sock`)

---

## Project Structure

```
CTF/
├── app/
│   ├── blueprints/
│   │   ├── admin.py          # Admin & maker panel
│   │   ├── auth.py           # Login, register, 2FA, password reset
│   │   ├── challenges.py     # Challenge list, flag submission
│   │   ├── docker.py         # Instance launch / extend / stop
│   │   └── main.py           # Home, leaderboard
│   ├── templates/
│   │   ├── docker/           # launch.html, instance_detail.html, my_instances.html
│   │   └── ...
│   ├── docker_manager.py     # DockerInstanceManager — spawns & kills containers
│   ├── instance_manager.py   # Scans CTF_Instances/ folders
│   ├── scheduler.py          # APScheduler — cleans up expired containers every 5 min
│   ├── models.py             # User, Challenge, DockerInstance, Solve, …
│   └── __init__.py           # App factory
├── CTF_Instances/
│   ├── Web_Instances/
│   │   └── xss-ashal/        # Example web challenge (Flask app + Dockerfile)
│   ├── Pwn_Instances/
│   └── Rev_Instances/
├── migrations/               # Alembic migration files
├── config.py
├── docker-compose.yml
├── Dockerfile
├── entrypoint.sh
├── requirements.txt
├── run.py
└── seed.py
```

---

## Running with Docker (recommended)

```bash
cd CTF
docker compose build --no-cache
docker compose up
```

The platform is available at **http://localhost:5000**.

Migrations run automatically on startup. The database is seeded with default admin/maker/hunter accounts on first run.

---

## Local Development (without Docker)

```bash
cd CTF
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux / Mac

pip install -r requirements.txt

# Copy and fill in environment variables
cp .env.example .env

flask db upgrade
python seed.py
python run.py
```

App runs at **http://localhost:5000** (HTTP only — set `SESSION_COOKIE_SECURE=false` in `.env` for local dev).

---

## Adding a New CTF Web Instance

Follow these steps every time you want to add a new launchable web challenge.

### 1 — Create the instance folder

```
CTF_Instances/Web_Instances/<your-instance-name>/
├── app.py            # Flask (or any WSGI) application
├── requirements.txt  # Dependencies including gunicorn
├── Dockerfile        # See template below
├── static/
├── templates/
└── instance/         # SQLite DB lives here (created at runtime)
```

**Minimal `Dockerfile` template:**

```dockerfile
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /app/instance
EXPOSE 80
CMD ["gunicorn", "--bind", "0.0.0.0:80", "--timeout", "60", "app:app"]
```

**`requirements.txt` must include `gunicorn`:**

```
Flask==2.2.5
gunicorn==21.2.0
```

### 2 — Build the Docker image

Run this once on the host that runs the platform (or in CI):

```bash
docker build -t cylvern/<your-instance-name> CTF_Instances/Web_Instances/<your-instance-name>/
```

The image name **must** follow the pattern `cylvern/<instance-folder-name>` — that is exactly what the platform passes to `docker run`.

### 3 — Create the challenge in the admin panel

1. Log in as admin → **Admin → Challenges → Add Challenge**
2. Set **Challenge Type** to `Web`
3. The **Instance** dropdown auto-populates with every folder found under `CTF_Instances/Web_Instances/` — select your new folder name
4. Fill in title, points, flag, description, then save

### 4 — Test it as a user

Log in as a regular user → open the challenge → click **🚀 Launch Instance**.

A personal container starts on a port in the `9000–10000` range with a **60-minute timer**. Users can extend up to 3 times (+30 min each). Expired containers are cleaned up automatically every 5 minutes by the background scheduler.

---

## Default Accounts (seeded)

| Role  | Username | Password   |
|-------|----------|------------|
| Admin | admin    | Admin@1234 |
| Maker | maker    | Maker@1234 |
| User  | hunter   | Hunt@12345 |

Change these immediately in production.

---

## Environment Variables

| Variable            | Required | Description                              |
|---------------------|----------|------------------------------------------|
| `SECRET_KEY`        | Yes (prod)| Flask session secret                    |
| `DATABASE_URL`      | Yes      | PostgreSQL connection string             |
| `MAIL_USERNAME`     | No       | SMTP username (email features disabled if unset) |
| `MAIL_PASSWORD`     | No       | SMTP password                            |
| `CLEANUP_API_KEY`   | No       | Protects `POST /docker/api/cleanup`      |

See `.env.example` for the full list.
