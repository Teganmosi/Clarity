"""
Sprint 12 migration: Add language/region/compliance to leads, create voice_call_logs.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "leads.db")


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(leads)")
    existing = {row[1] for row in cursor.fetchall()}

    for col_name, col_type in [("preferred_language", "VARCHAR(10) DEFAULT 'en'"),
                                ("region", "VARCHAR(20)"),
                                ("compliance_flags", "TEXT DEFAULT '{}'")]:
        if col_name not in existing:
            cursor.execute(f"ALTER TABLE leads ADD COLUMN {col_name} {col_type}")
            print(f"Added column to leads: {col_name}")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS voice_call_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER NOT NULL,
            status VARCHAR(20) DEFAULT 'initiated',
            phone_number VARCHAR(30),
            language VARCHAR(10) DEFAULT 'en',
            transcript TEXT,
            recording_url VARCHAR(500),
            call_summary TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lead_id) REFERENCES leads(id)
        )
    """)
    print("Created voice_call_logs table")

    conn.commit()
    conn.close()
    print("Sprint 12 migration complete.")


if __name__ == "__main__":
    migrate()
