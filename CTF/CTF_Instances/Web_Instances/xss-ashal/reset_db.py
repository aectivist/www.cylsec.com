import sqlite3
import os

# Path to your database
DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'ashal.db')

def reset_database():
    if not os.path.exists(DB_PATH):
        print("❌ Database not found. Nothing to reset.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Delete all inscriptions (the wall)
    cursor.execute("DELETE FROM inscriptions")
    print("✅ All inscriptions deleted.")

    # (Optional) Reset all user progress – uncomment if you want to reset solved flags as well
    # cursor.execute("DELETE FROM user_progress")
    # print("✅ All user progress reset.")

    conn.commit()
    conn.close()
    print("✅ Database reset complete.")

if __name__ == '__main__':
    reset_database()