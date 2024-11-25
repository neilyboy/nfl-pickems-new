import sqlite3
import os

def init_sqlite():
    # Ensure instance directory exists
    os.makedirs('instance', exist_ok=True)
    
    # Create database file
    conn = sqlite3.connect('instance/app.db')
    conn.close()
    
    print("SQLite database file created successfully!")

if __name__ == '__main__':
    init_sqlite()
