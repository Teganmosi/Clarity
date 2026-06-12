"""
Sprint 1 Database Migration Script
Adds enrichment fields to the Lead model
"""

import os
import sys
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "leads.db"


def run_migration():
    if not DB_PATH.exists():
        print(f"[INFO] Database not found at {DB_PATH}. Will be created on app startup.")
        return

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(leads)")
    existing_columns = {row[1] for row in cursor.fetchall()}

    new_columns = {
        "technologies": "JSON DEFAULT '[]'",
        "funding_stage": "VARCHAR(50)",
        "employee_count": "INTEGER",
        "logo_url": "VARCHAR(500)",
        "linkedin_url": "VARCHAR(500)",
        "twitter_handle": "VARCHAR(100)",
        "annual_revenue": "VARCHAR(50)",
        "headquarters_location": "VARCHAR(200)",
        "founded_year": "INTEGER",
        "industry_tags": "JSON DEFAULT '[]'",
        "tech_stack_last_updated": "DATETIME",
        "enrichment_status": "VARCHAR(20) DEFAULT 'pending'",
        "enrichment_source": "VARCHAR(50)",
        "last_enriched_at": "DATETIME",
    }

    added = 0
    for col_name, col_def in new_columns.items():
        if col_name not in existing_columns:
            try:
                cursor.execute(f"ALTER TABLE leads ADD COLUMN {col_name} {col_def}")
                print(f"  [ADDED] {col_name}")
                added += 1
            except Exception as e:
                print(f"  [ERROR] {col_name}: {e}")

    conn.commit()
    conn.close()

    if added > 0:
        print(f"\n[SUCCESS] Added {added} new enrichment fields to Lead model")
    else:
        print("\n[OK] All enrichment fields already exist")


if __name__ == "__main__":
    run_migration()
