import sqlite3
import os

os.makedirs("database", exist_ok=True)

conn = sqlite3.connect("database/users.db")
cursor = conn.cursor()

# Create table with fields specified in user prompt
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    contact1 TEXT,
    contact2 TEXT
)
""")

conn.commit()
conn.close()

print("Database created successfully")