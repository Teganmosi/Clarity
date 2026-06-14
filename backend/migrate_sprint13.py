"""
Sprint 13 migration: Create anonymized_outcomes and network_insights tables.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "leads.db")


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS anonymized_outcomes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hashed_identifier VARCHAR(64),
            industry_tag VARCHAR(100),
            funding_stage VARCHAR(50),
            action VARCHAR(100),
            action_type VARCHAR(50),
            success BOOLEAN DEFAULT 0,
            channel VARCHAR(20) DEFAULT 'email',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("Created anonymized_outcomes table")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS network_insights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            segment TEXT DEFAULT '{}',
            insight_type VARCHAR(50),
            metric_value FLOAT,
            confidence FLOAT DEFAULT 0.0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("Created network_insights table")

    conn.commit()
    conn.close()
    print("Sprint 13 migration complete.")


if __name__ == "__main__":
    migrate()
