import sqlite3
from datetime import datetime

DB_PATH = "karwan_tijarat.db"

def init_db():
    """Initialize the database with required tables"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS members
                 (id TEXT PRIMARY KEY,
                  full_name TEXT NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  phone TEXT,
                  profession TEXT NOT NULL,
                  expertise TEXT NOT NULL,
                  how_to_help TEXT NOT NULL,
                  linkedin_url TEXT,
                  social_media TEXT,
                  photo BLOB,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def save_profile(profile_data):
    """Save or update a profile"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        c.execute('''INSERT OR REPLACE INTO members 
                     (id, full_name, email, phone, profession, expertise, 
                      how_to_help, linkedin_url, social_media, photo) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (profile_data['id'], profile_data['full_name'], 
                   profile_data['email'], profile_data['phone'],
                   profile_data['profession'], profile_data['expertise'],
                   profile_data['how_to_help'], profile_data['linkedin_url'],
                   profile_data['social_media'], profile_data.get('photo')))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        conn.close()

def get_profile_by_email(email):
    """Retrieve profile by email"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # For dictionary-like access
    c = conn.cursor()
    
    try:
        c.execute("SELECT * FROM members WHERE email=?", (email,))
        return c.fetchone()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        conn.close()

def search_profiles(search_term):
    """Search profiles by name, profession or expertise"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        c.execute("""SELECT full_name, profession, expertise, email, phone, 
                      linkedin_url, social_media 
                   FROM members 
                   WHERE full_name LIKE ? OR profession LIKE ? OR expertise LIKE ?""",
                   (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
        return c.fetchall()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        conn.close()

def export_to_csv():
    """Export all data to pandas DataFrame"""
    conn = sqlite3.connect(DB_PATH)
    try:
        return pd.read_sql_query("SELECT * FROM members", conn)
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        conn.close()

# Initialize the database when this module is imported
init_db()
