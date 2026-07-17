from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response, g
import sqlite3
import os
import time

app = Flask(__name__)
app.secret_key = 'ashal-secret-key'

if not os.path.exists(app.instance_path):
    os.makedirs(app.instance_path)

DATABASE = os.path.join(app.instance_path, 'ashal.db')

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS inscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT,
                message TEXT,
                timestamp TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS user_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                solved_area_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, solved_area_id)
            )
        ''')
        db.commit()

init_db()

FLAGS = {
    1: 'FLAG{ASHAL_XSS_ALERT}',
    2: 'FLAG{ASHAL_XSS_COOKIE_STOLEN}',
    3: 'FLAG{ASHAL_XSS_SESSION_HIJACK}',
    4: 'FLAG{ASHAL_XSS_KEYLOGGER}',
    5: 'FLAG{ASHAL_XSS_DEFACEMENT_TARGETED}'
}

AREAS = [
    {"id": 1, "name": "Basic Alert", "flag": FLAGS[1], "check": lambda msg: "alert(" in msg, "payload_hint": "<script>alert(1)</script>"},
    {"id": 2, "name": "Cookie Stealing", "flag": FLAGS[2], "check": lambda msg: "document.cookie" in msg, "payload_hint": "<script>alert(document.cookie)</script>"},
    {"id": 3, "name": "Session Hijacking", "flag": FLAGS[3], "check": lambda msg: "fetch" in msg or "XMLHttpRequest" in msg, "payload_hint": "<script>fetch('/update_status',{method:'POST',body:'status=hacked'})</script>"},
    {"id": 4, "name": "Keylogging", "flag": FLAGS[4], "check": lambda msg: "onkeypress" in msg, "payload_hint": "<script>document.onkeypress=function(e){alert(e.key)}</script>"},
    {"id": 5, "name": "Targeted Defacement", "flag": FLAGS[5], "check": lambda msg: "getElementById" in msg and "innerHTML" in msg, "payload_hint": "<script>document.getElementById('inscriptions-container').innerHTML = '<h1>Defaced!</h1>'</script>"}
]

SERIALIZABLE_AREAS = [{"id": a["id"], "name": a["name"], "flag": a["flag"]} for a in AREAS]

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    db = get_db()
    user_id = session['user_id']
    user_row = db.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user_row:
        session.pop('user_id', None)
        flash('Your session has expired. Please log in again.', 'warning')
        return redirect(url_for('login_page'))
    username = user_row['username']
    solved_rows = db.execute("SELECT solved_area_id FROM user_progress WHERE user_id = ?", (user_id,)).fetchall()
    solved = [row['solved_area_id'] for row in solved_rows]
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        message = request.form.get('message', '').strip()
        if name and message:
            db.execute("INSERT INTO inscriptions (user_id, name, message, timestamp) VALUES (?, ?, ?, ?)", (user_id, name, message, time.strftime('%Y-%m-%d %H:%M:%S')))
            db.commit()
            for area in AREAS:
                if area['id'] not in solved and area['check'](message):
                    db.execute("INSERT INTO user_progress (user_id, solved_area_id) VALUES (?, ?)", (user_id, area['id']))
                    db.commit()
                    solved.append(area['id'])
                    flash(f'Flag captured: {area["flag"]} ({area["name"]})', 'success')
        return redirect(url_for('index'))
    inscriptions = db.execute("SELECT name, message, timestamp FROM inscriptions WHERE user_id = ? ORDER BY id DESC", (user_id,)).fetchall()
    resp = make_response(render_template('index.html', inscriptions=inscriptions, areas=SERIALIZABLE_AREAS, solved=solved, username=username))
    resp.set_cookie('flag', 'FLAG{ASHAL_XSS_COOKIE_STOLEN}', httponly=False)
    return resp

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        if not username:
            flash('Please enter a username.', 'warning')
            return render_template('login.html')
        db = get_db()
        user = db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if user:
            session['user_id'] = user['id']
            flash(f'Welcome back, {username}!', 'success')
        else:
            cursor = db.execute("INSERT INTO users (username) VALUES (?)", (username,))
            db.commit()
            session['user_id'] = cursor.lastrowid
            flash(f'Welcome, {username}!', 'success')
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out.', 'info')
    return redirect(url_for('login_page'))

@app.route('/reset')
def reset():
    db = get_db()
    db.execute("DELETE FROM inscriptions WHERE user_id = ?", (session.get('user_id'),))
    db.commit()
    flash('Your wall has been cleansed.', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)
