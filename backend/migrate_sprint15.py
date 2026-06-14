"""
Sprint 15 migration: Add churn/expansion fields to accounts, create health_snapshots table.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "leads.db")


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(accounts)")
    existing = {row[1] for row in cursor.fetchall()}

    for col_name, col_type in [("churn_risk_score", "INTEGER DEFAULT 0"),
                                ("expansion_score", "INTEGER DEFAULT 0"),
                                ("health_status", "VARCHAR(20) DEFAULT 'healthy'"),
                                ("last_health_check", "DATETIME")]:
        if col_name not in existing:
            cursor.execute(f"ALTER TABLE accounts ADD COLUMN {col_name} {col_type}")
            print(f"Added column to accounts: {col_name}")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS health_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            health_score INTEGER,
            churn_risk INTEGER,
            expansion_score INTEGER,
            snapshot_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_id) REFERENCES accounts(id)
        )
    """)
    print("Created health_snapshots table")

    conn.commit()
    conn.close()
    print("Sprint 15 migration complete.")


if __name__ == "__main__":
    migrate()
