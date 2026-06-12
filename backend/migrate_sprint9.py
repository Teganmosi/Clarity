"""
Sprint 9 migration: Add lifecycle fields to leads, create agent_execution_logs table.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "leads.db")


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(leads)")
    existing = {row[1] for row in cursor.fetchall()}

    for col_name, col_type in [("lifecycle_stage", "VARCHAR(30) DEFAULT 'new'"),
                                ("active_agent", "VARCHAR(30)")]:
        if col_name not in existing:
            cursor.execute(f"ALTER TABLE leads ADD COLUMN {col_name} {col_type}")
            print(f"Added column to leads: {col_name}")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_execution_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER NOT NULL,
            previous_stage VARCHAR(30),
            new_stage VARCHAR(30),
            trigger_reason TEXT,
            assigned_agent VARCHAR(30),
            action VARCHAR(200),
            outcome VARCHAR(100),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lead_id) REFERENCES leads(id)
        )
    """)
    print("Created agent_execution_logs table")

    conn.commit()
    conn.close()
    print("Sprint 9 migration complete.")


if __name__ == "__main__":
    migrate()
