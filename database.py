import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "karwan_tijarat.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS members
                 (id TEXT PRIMARY KEY,
                  full_name TEXT NOT NULL DEFAULT '',
                  profession TEXT NOT NULL DEFAULT '',
                  expertise TEXT NOT NULL DEFAULT '',
                  email TEXT UNIQUE NOT NULL,
                  phone TEXT DEFAULT '',
                  location TEXT DEFAULT '',
                  experience INTEGER DEFAULT 0,
                  can_help TEXT NOT NULL DEFAULT '',
                  needs_help TEXT DEFAULT '',
                  bio TEXT DEFAULT '',
                  password TEXT NOT NULL,
                  profile_pic TEXT DEFAULT '',
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()
