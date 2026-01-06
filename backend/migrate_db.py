"""
Database migration script to add missing columns
"""

import sqlite3
import os
import sys

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

db_path = os.path.join(os.path.dirname(__file__), 'leads.db')

print(f"Checking database at: {db_path}")

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if hashed_password column exists
cursor.execute("PRAGMA table_info(users)")
columns = [row[1] for row in cursor.fetchall()]

print(f"Current columns in users table: {columns}")

# Add missing columns if they don't exist
if 'hashed_password' not in columns:
    print("Adding hashed_password column...")
    cursor.execute("ALTER TABLE users ADD COLUMN hashed_password VARCHAR(255)")
    conn.commit()
    print("[OK] hashed_password column added")
else:
    print("[OK] hashed_password column already exists")

# Check if leads table has all required columns
cursor.execute("PRAGMA table_info(leads)")
lead_columns = [row[1] for row in cursor.fetchall()]

print(f"Current columns in leads table: {lead_columns}")

required_lead_columns = [
    'id', 'user_id', 'name', 'email', 'company', 'phone', 'title',
    'source', 'campaign', 'medium', 'past_interactions', 'last_interaction_date',
    'pages_visited', 'time_on_site', 'company_size', 'industry', 'budget',
    'score', 'score_category', 'conversion_probability', 'status', 'converted',
    'conversion_date', 'hubspot_id', 'pipedrive_id', 'notes', 'tags',
    'created_at', 'updated_at'
]

for col in required_lead_columns:
    if col not in lead_columns:
        print(f"Adding {col} column to leads table...")
        cursor.execute(f"ALTER TABLE leads ADD COLUMN {col} TEXT")
        conn.commit()
        print(f"[OK] {col} column added")

# Check if notification_logs table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='notification_logs'")
if not cursor.fetchone():
    print("Creating notification_logs table...")
    cursor.execute("""
        CREATE TABLE notification_logs (
            id INTEGER PRIMARY KEY,
            lead_id INTEGER,
            notification_type VARCHAR(20),
            recipient VARCHAR(200),
            subject VARCHAR(200),
            message TEXT,
            status VARCHAR(20),
            error_message TEXT,
            sent_at TIMESTAMP
        )
    """)
    conn.commit()
    print("[OK] notification_logs table created")
else:
    print("[OK] notification_logs table already exists")

# Check if integration_logs table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='integration_logs'")
if not cursor.fetchone():
    print("Creating integration_logs table...")
    cursor.execute("""
        CREATE TABLE integration_logs (
            id INTEGER PRIMARY KEY,
            lead_id INTEGER,
            integration_type VARCHAR(20),
            action VARCHAR(50),
            external_id VARCHAR(50),
            request_data TEXT,
            response_data TEXT,
            status VARCHAR(20),
            error_message TEXT,
            created_at TIMESTAMP
        )
    """)
    conn.commit()
    print("[OK] integration_logs table created")
else:
    print("[OK] integration_logs table already exists")

conn.close()
print("\n[SUCCESS] Database migration completed successfully!")
