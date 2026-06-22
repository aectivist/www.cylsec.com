### How to Run

Create a virtual environment:
------------
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

Install dependencies:
------------
pip install -r requirements.txt

Set up Flask-Migrate (optional, but recommended):
------------
export FLASK_APP=run.py
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

Seed the database:
------------
python seed.py

Run the app:
------------
python run.py

------------
Visit http://127.0.0.1:5000.