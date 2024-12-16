"""
Database Initialization Script

This script creates the SQLite database and initializes the schema for the image processor project.
"""

import sqlite3
import os

# Database file path
DB_PATH = os.path.join(os.path.dirname(__file__), "image_descriptions.db")

def initialize_database():
    """Create the SQLite database and initialize the schema."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create the image_descriptions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS image_descriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filepath TEXT NOT NULL,
        description TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    conn.commit()
    conn.close()

    print(f"Database initialized at {DB_PATH}")

if __name__ == "__main__":
    initialize_database()
