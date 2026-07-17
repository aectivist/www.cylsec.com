from app import create_app
import os

app = create_app()

if __name__ == '__main__':
    # Never enable debug=True in production. Honor env var override for local testing.
    debug = os.environ.get('FLASK_DEBUG', '0') in ['1', 'true', 'True']
    app.run(debug=debug, host='127.0.0.1')