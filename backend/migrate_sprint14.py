"""
Sprint 14 migration: Create deals and contract_logs tables.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "leads.db")


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS deals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER NOT NULL,
            value FLOAT DEFAULT 0.0,
            currency VARCHAR(10) DEFAULT 'USD',
            contract_content TEXT,
            status VARCHAR(20) DEFAULT 'draft',
            signing_url VARCHAR(500),
            payment_link VARCHAR(500),
            payment_intent_id VARCHAR(100),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            signed_at DATETIME,
            paid_at DATETIME,
            FOREIGN KEY (lead_id) REFERENCES leads(id)
        )
    """)
    print("Created deals table")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contract_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            deal_id INTEGER NOT NULL,
            action VARCHAR(50),
            details TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (deal_id) REFERENCES deals(id)
        )
    """)
    print("Created contract_logs table")

    conn.commit()
    conn.close()
    print("Sprint 14 migration complete.")


if __name__ == "__main__":
    migrate()
