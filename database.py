import sqlite3
from uuid import uuid4

def init_db():
    conn = sqlite3.connect('karwan_tijarat.db')
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
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()
