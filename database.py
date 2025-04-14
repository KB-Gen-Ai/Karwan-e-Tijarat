import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "karwan_tijarat.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS members
                 (id TEXT PRIMARY KEY,
                  full_name TEXT NOT NULL,
                  profession TEXT NOT NULL,
                  expertise TEXT NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  phone TEXT,
                  location TEXT,
                  experience INTEGER,
                  can_help TEXT NOT NULL,
                  needs_help TEXT,
                  bio TEXT,
                  password TEXT,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()
