"""
Sprint 5 migration: Create email_outreach table.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "leads.db")


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_outreach (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER NOT NULL,
            subject VARCHAR(200),
            body TEXT,
            status VARCHAR(20) DEFAULT 'draft',
            sent_at DATETIME,
            opened_at DATETIME,
            ai_model_used VARCHAR(50),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lead_id) REFERENCES leads(id)
        )
    """)
    print("Created email_outreach table")

    conn.commit()
    conn.close()
    print("Sprint 5 migration complete.")


if __name__ == "__main__":
    migrate()
