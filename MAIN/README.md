# CYLVERN MAIN — Marketing & Info Site

Separate Flask app serving the public marketing site for cylsec.com.

## Structure

```
MAIN/
├── app.py                # Flask application (all routes in one file)
├── requirements.txt
├── .env.example
├── entrypoint.sh
├── static/
│   └── css/style.css
└── templates/
    ├── base.html
    ├── index.html
    ├── individuals.html
    ├── business.html
    ├── wip.html
    ├── admin/
    │   ├── login.html
    │   └── panel.html
    └── errors/
        ├── 403.html
        ├── 404.html
        └── 500.html
```

## Running locally

```bash
cd MAIN
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # Linux/Mac
pip install -r requirements.txt
cp .env.example .env       # edit .env with your values
python app.py
```

Runs at **http://localhost:5001**

## Admin panel

`/admin/login` — sign in with credentials set in `.env` (`ADMIN_USERNAME` / `ADMIN_PASSWORD`).

The admin panel has one function: **manage the site-wide alert banner** that appears at the top of every page. Set the message, level (info / warning / danger), and toggle visibility.

Incoming business inquiries are also listed in the panel.

## Pages

| URL                         | Page                                |
|-----------------------------|-------------------------------------|
| `/`                         | Home — about, mission, values       |
| `/individuals`              | Individual overview                 |
| `/individuals/ctf`          | CTF — WIP redirect                  |
| `/individuals/academy`      | Academy — WIP redirect              |
| `/individuals/mentorship`   | Private Mentorship — WIP redirect   |
| `/business`                 | Business & public sector + inquiry form |
| `/admin/login`              | Admin login                         |
| `/admin`                    | Admin panel (alert + inbox)         |
