"""
Sprint 7 migration: Create conversations table.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "leads.db")


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER NOT NULL,
            channel VARCHAR(20) DEFAULT 'chat',
            messages TEXT DEFAULT '[]',
            bant_scores TEXT DEFAULT '{}',
            status VARCHAR(20) DEFAULT 'active',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME,
            FOREIGN KEY (lead_id) REFERENCES leads(id)
        )
    """)
    print("Created conversations table")

    conn.commit()
    conn.close()
    print("Sprint 7 migration complete.")


if __name__ == "__main__":
    migrate()
