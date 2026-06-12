"""
Sprint 6 migration: Create communication_logs and global_suppressions tables.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "leads.db")


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS communication_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER NOT NULL,
            channel VARCHAR(20) NOT NULL,
            status VARCHAR(20) DEFAULT 'sent',
            subject VARCHAR(200),
            body TEXT,
            message_id VARCHAR(100),
            sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lead_id) REFERENCES leads(id)
        )
    """)
    print("Created communication_logs table")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS global_suppressions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email VARCHAR(200),
            phone VARCHAR(50),
            reason VARCHAR(100) DEFAULT 'user_request',
            added_by VARCHAR(100),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("Created global_suppressions table")

    conn.commit()
    conn.close()
    print("Sprint 6 migration complete.")


if __name__ == "__main__":
    migrate()
