"""
Sprint 3 migration: Add predictive analytics fields and workflows table.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "leads.db")


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    new_lead_columns = [
        ("predicted_closure_prob", "FLOAT DEFAULT 0.0"),
        ("estimated_clv", "FLOAT DEFAULT 0.0"),
        ("forecast_close_date", "VARCHAR(20)"),
    ]

    cursor.execute("PRAGMA table_info(leads)")
    existing = {row[1] for row in cursor.fetchall()}

    for col_name, col_type in new_lead_columns:
        if col_name not in existing:
            cursor.execute(f"ALTER TABLE leads ADD COLUMN {col_name} {col_type}")
            print(f"Added column to leads: {col_name} ({col_type})")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workflows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name VARCHAR(200) NOT NULL,
            trigger_field VARCHAR(100) NOT NULL,
            trigger_operator VARCHAR(50) NOT NULL,
            trigger_value VARCHAR(200) NOT NULL,
            action_type VARCHAR(50) NOT NULL,
            action_params TEXT DEFAULT '{}',
            active BOOLEAN DEFAULT 1,
            created_at VARCHAR(30)
        )
    """)
    print("Created workflows table")

    conn.commit()
    conn.close()
    print("Sprint 3 migration complete.")


if __name__ == "__main__":
    migrate()
