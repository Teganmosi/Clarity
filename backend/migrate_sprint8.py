"""
Sprint 8 migration: Create meetings table.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "leads.db")


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meetings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER NOT NULL,
            scheduled_time DATETIME NOT NULL,
            duration_minutes INTEGER DEFAULT 30,
            timezone VARCHAR(50) DEFAULT 'UTC',
            status VARCHAR(20) DEFAULT 'scheduled',
            meeting_link VARCHAR(500),
            ics_content TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lead_id) REFERENCES leads(id)
        )
    """)
    print("Created meetings table")

    conn.commit()
    conn.close()
    print("Sprint 8 migration complete.")


if __name__ == "__main__":
    migrate()
