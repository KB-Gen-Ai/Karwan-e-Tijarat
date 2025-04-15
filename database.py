import sqlite3
import re

# Database setup
conn = sqlite3.connect('karwan_e_tijarat.db', check_same_thread=False)
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        phone TEXT,
        city TEXT,
        profession TEXT,
        skills TEXT,
        help_offer TEXT,
        help_seek TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()

def validate_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def validate_phone(phone):
    return re.match(r"^[0-9\-\+]{9,15}$", phone)

def get_profile_by_email_phone(email, phone):
    c.execute("SELECT * FROM profiles WHERE email = ? AND phone = ?", (email, phone))
    return c.fetchone()

def insert_or_update_profile(data):
    existing = get_profile_by_email_phone(data['email'], data['phone'])
    if existing:
        c.execute('''
            UPDATE profiles SET name=?, city=?, profession=?, skills=?, help_offer=?, help_seek=?, timestamp=CURRENT_TIMESTAMP
            WHERE email=? AND phone=?
        ''', (data['name'], data['city'], data['profession'], data['skills'], data['help_offer'], data['help_seek'], data['email'], data['phone']))
    else:
        c.execute('''
            INSERT INTO profiles (name, email, phone, city, profession, skills, help_offer, help_seek)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (data['name'], data['email'], data['phone'], data['city'], data['profession'], data['skills'], data['help_offer'], data['help_seek']))
    conn.commit()

def fetch_profiles_by_search(search_term):
    c.execute("""
        SELECT * FROM profiles
        WHERE name LIKE ? OR city LIKE ? OR profession LIKE ?
        ORDER BY timestamp DESC
    """, (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
    return c.fetchall()

def fetch_all_profiles():
    return c.execute("SELECT * FROM profiles").fetchall()

def get_connection():
    return conn
