import sqlite3
from typing import Optional, List, Dict, Any

DB_PATH = "karwan_tijarat.db"
SCHEMA_VERSION = 2  # Increment this when schema changes

def init_db():
    """Initialize database with proper schema"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Create version table if not exists
    c.execute("CREATE TABLE IF NOT EXISTS db_version (version INTEGER)")
    
    # Get current version
    c.execute("SELECT version FROM db_version LIMIT 1")
    result = c.fetchone()
    current_version = result[0] if result else 0
    
    # Create members table with all columns
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
    
    # Upgrade schema if needed
    if current_version < SCHEMA_VERSION:
        try:
            # Add missing columns
            c.execute("PRAGMA table_info(members)")
            columns = [col[1] for col in c.fetchall()]
            
            if 'linkedin_url' not in columns:
                c.execute("ALTER TABLE members ADD COLUMN linkedin_url TEXT")
            
            if 'social_media' not in columns:
                c.execute("ALTER TABLE members ADD COLUMN social_media TEXT")
                
            if 'photo' not in columns:
                c.execute("ALTER TABLE members ADD COLUMN photo BLOB")
            
            # Update version
            c.execute("DELETE FROM db_version")
            c.execute("INSERT INTO db_version (version) VALUES (?)", (SCHEMA_VERSION,))
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            raise RuntimeError(f"Database upgrade failed: {str(e)}")
    
    conn.commit()
    conn.close()
