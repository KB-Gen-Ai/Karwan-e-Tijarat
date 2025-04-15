import sqlite3
import pandas as pd
import uuid

DB_PATH = "karwan_tijarat.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS members
                 (id TEXT PRIMARY KEY,
                  full_name TEXT NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  city TEXT NOT NULL,
                  country TEXT NOT NULL,
                  primary_phone TEXT NOT NULL,
                  secondary_phone TEXT,
                  profession TEXT NOT NULL,
                  expertise TEXT NOT NULL,
                  how_to_help TEXT NOT NULL,
                  help_needed TEXT NOT NULL,
                  business_url TEXT,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def migrate_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        c.execute("ALTER TABLE members ADD COLUMN help_needed TEXT NOT NULL DEFAULT ''")
    except sqlite3.OperationalError:
        pass
    
    conn.commit()
    conn.close()

def get_profile_by_id(profile_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM members WHERE id=?", (profile_id,))
    result = c.fetchone()
    conn.close()
    return dict(result) if result else None

def get_profile_by_email(email):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM members WHERE email=?", (email,))
    result = c.fetchone()
    conn.close()
    return dict(result) if result else None

def save_profile(profile_data):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''INSERT OR REPLACE INTO members 
                    (id, full_name, email, city, country, primary_phone, 
                     secondary_phone, profession, expertise, how_to_help, 
                     help_needed, business_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                 (profile_data['id'], profile_data['full_name'], profile_data['email'],
                  profile_data['city'], profile_data['country'], 
                  profile_data['primary_phone'], profile_data.get('secondary_phone', ''),
                  profile_data['profession'], profile_data['expertise'], 
                  profile_data['how_to_help'], profile_data.get('help_needed', ''),
                  profile_data.get('business_url', '')))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        conn.close()

def get_all_profiles():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM members", conn)
    conn.close()
    return df

def search_profiles(search_term):
    conn = sqlite3.connect(DB_PATH)
    query = f"%{search_term.lower()}%"
    df = pd.read_sql_query('''SELECT * FROM members 
                            WHERE LOWER(full_name) LIKE ? 
                            OR LOWER(profession) LIKE ? 
                            OR LOWER(expertise) LIKE ? 
                            OR LOWER(city) LIKE ? 
                            OR LOWER(country) LIKE ?''', 
                          conn, params=(query,)*5)
    conn.close()
    return df
