"""
Sprint 4 migration: Add delay_minutes to workflows, create workflow_logs table.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "leads.db")


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(workflows)")
    existing = {row[1] for row in cursor.fetchall()}

    if "delay_minutes" not in existing:
        cursor.execute("ALTER TABLE workflows ADD COLUMN delay_minutes INTEGER DEFAULT 0")
        print("Added delay_minutes to workflows")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workflow_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_id INTEGER NOT NULL,
            rule_name VARCHAR(200),
            lead_id INTEGER NOT NULL,
            lead_name VARCHAR(200),
            action_type VARCHAR(50),
            status VARCHAR(20),
            execution_time FLOAT DEFAULT 0.0,
            step_details TEXT,
            error_message TEXT,
            timestamp VARCHAR(30)
        )
    """)
    print("Created workflow_logs table")

    conn.commit()
    conn.close()
    print("Sprint 4 migration complete.")


if __name__ == "__main__":
    migrate()
