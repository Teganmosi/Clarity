"""
Sprint 10 migration: Create outcome_logs and ab_tests tables.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "leads.db")


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS outcome_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER NOT NULL,
            action_id VARCHAR(100),
            outcome_type VARCHAR(50),
            value FLOAT DEFAULT 1.0,
            extra_data TEXT DEFAULT '{}',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lead_id) REFERENCES leads(id)
        )
    """)
    print("Created outcome_logs table")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ab_tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(200),
            variant_a TEXT DEFAULT '{}',
            variant_b TEXT DEFAULT '{}',
            metric VARCHAR(50) DEFAULT 'reply_rate',
            winner VARCHAR(10),
            status VARCHAR(20) DEFAULT 'running',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("Created ab_tests table")

    conn.commit()
    conn.close()
    print("Sprint 10 migration complete.")


if __name__ == "__main__":
    migrate()
