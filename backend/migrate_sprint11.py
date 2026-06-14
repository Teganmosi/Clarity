"""
Sprint 11 migration: Create accounts, role_permissions tables; add account_id to leads.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "leads.db")


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name VARCHAR(200) NOT NULL,
            domain VARCHAR(200),
            industry VARCHAR(100),
            total_revenue FLOAT DEFAULT 0.0,
            employee_count INTEGER,
            health_score INTEGER DEFAULT 0,
            buying_stage VARCHAR(30) DEFAULT 'awareness',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("Created accounts table")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS role_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role VARCHAR(30) DEFAULT 'sdr',
            can_view_all_leads BOOLEAN DEFAULT 0,
            can_delete_leads BOOLEAN DEFAULT 0,
            can_manage_users BOOLEAN DEFAULT 0,
            can_edit_global_settings BOOLEAN DEFAULT 0,
            can_view_analytics BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    print("Created role_permissions table")

    cursor.execute("PRAGMA table_info(leads)")
    existing = {row[1] for row in cursor.fetchall()}
    if "account_id" not in existing:
        cursor.execute("ALTER TABLE leads ADD COLUMN account_id INTEGER REFERENCES accounts(id)")
        print("Added account_id to leads")

    conn.commit()
    conn.close()
    print("Sprint 11 migration complete.")


if __name__ == "__main__":
    migrate()
