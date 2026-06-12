"""
Sprint 2 migration: Add intent detection fields to the Lead model.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "leads.db")


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    new_columns = [
        ("intent_score", "INTEGER DEFAULT 0"),
        ("last_intent_check", "DATETIME"),
        ("intent_signals", "JSON DEFAULT '[]'"),
    ]

    cursor.execute("PRAGMA table_info(leads)")
    existing = {row[1] for row in cursor.fetchall()}

    for col_name, col_type in new_columns:
        if col_name not in existing:
            cursor.execute(f"ALTER TABLE leads ADD COLUMN {col_name} {col_type}")
            print(f"Added column: {col_name} ({col_type})")

    conn.commit()
    conn.close()
    print("Sprint 2 migration complete.")


if __name__ == "__main__":
    migrate()
