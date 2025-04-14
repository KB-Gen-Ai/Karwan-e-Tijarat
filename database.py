import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "karwan_tijarat.db")

def init_db():
    """Initialize database with required tables"""
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
                  password TEXT,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def save_profile(profile_data):
    """Save or update user profile"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''INSERT OR REPLACE INTO members 
                 (id, full_name, email, phone, profession, expertise, how_to_help) 
                 VALUES (?, ?, ?, ?, ?, ?, ?)''',
              (profile_data['id'],
               profile_data['full_name'],
               profile_data['email'],
               profile_data['phone'],
               profile_data['profession'],
               profile_data['expertise'],
               profile_data['how_to_help']))
    conn.commit()
    conn.close()

def get_profile_by_id(profile_id):
    """Retrieve profile by ID"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT * FROM members WHERE id=?", (profile_id,))
    result = c.fetchone()
    conn.close()
    
    if result:
        return {
            'id': result[0],
            'full_name': result[1],
            'email': result[2],
            'phone': result[3],
            'profession': result[4],
            'expertise': result[5],
            'how_to_help': result[6]
        }
    return None

def get_profile_by_email(email):
    """Retrieve profile by email (for auth)"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT * FROM members WHERE email=?", (email,))
    result = c.fetchone()
    conn.close()
    
    if result:
        return {
            'id': result[0],
            'full_name': result[1],
            'email': result[2],
            'password': result[7]  # For authentication
        }
    return None
