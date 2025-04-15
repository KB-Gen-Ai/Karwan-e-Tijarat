import sqlite3

# Create a new database connection
conn = sqlite3.connect('karwan_e_tijarat.db', check_same_thread=False)
c = conn.cursor()

# Update the table schema to include the 'country' column
c.execute('''
    CREATE TABLE IF NOT EXISTS profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        phone TEXT,
        city TEXT,
        country TEXT,  -- New column for country
        profession TEXT,
        skills TEXT,
        help_offer TEXT,
        help_seek TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')

# Commit changes to the database
conn.commit()
