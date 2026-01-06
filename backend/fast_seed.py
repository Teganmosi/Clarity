import sqlite3
import json
import os
from datetime import datetime

# Adjust paths if necessary (running from 'backend' dir)
DB_PATH = 'leads.db'
JSON_PATH = '../sample-leads.json'

def seed():
    if not os.path.exists(DB_PATH):
        print(f"Error: {DB_PATH} not found in current directory.")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 1. Get ALL users
    try:
        c.execute("SELECT id, username FROM users")
        users = c.fetchall()
    except sqlite3.OperationalError as e:
         print(f"Error: Database check failed ({e}). Check if tables exist.")
         return

    if not users:
        print("Creating default user...")
        now_str = datetime.now().isoformat()
        try:
            c.execute("""
                INSERT INTO users (username, email, hashed_password, api_key, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ('admin', 'admin@example.com', 'dummy_hash', 'test-api-key', 1, now_str))
            users = [(c.lastrowid, 'admin')]
            conn.commit()
        except Exception as e:
            print(f"Failed to create user: {e}")
            return

    print(f"Found {len(users)} users. Seeding data for all of them...")

    # 2. Load JSON
    target_json_path = JSON_PATH
    if not os.path.exists(target_json_path):
        # Try finding it in root if we are in backend
        alt_path = 'sample-leads.json'
        if os.path.exists(alt_path):
             target_json_path = alt_path
        else:
             print(f"Error: {target_json_path} not found.")
             print("Current Dir:", os.getcwd())
             return

    with open(target_json_path, 'r') as f:
        leads = json.load(f)

    # 3. Insert leads for EACH user
    total_added = 0
    
    for user_id, username in users:
        print(f"  > Processing user: {username} (ID: {user_id})")
        user_count = 0
        for lead in leads:
            # Check existing for THIS user
            c.execute("SELECT id FROM leads WHERE email = ? AND user_id = ?", (lead['email'], user_id))
            existing_row = c.fetchone()
            
            now_str = datetime.now().isoformat()

            if existing_row:
                # Update created_at to NOW so it shows up in Date-filtered charts (Trends, Recent Activity)
                lead_id = existing_row[0]
                c.execute("UPDATE leads SET created_at = ? WHERE id = ?", (now_str, lead_id))
                continue

            # Dummy scores for visualization
            score = 65.2
            category = 'warm'
            status = 'new'
            
            src = lead.get('source', '')
            if 'referral' in src or 'partner' in src:
                score = 88.5
                category = 'hot'
            elif 'website' in src and lead.get('pages_visited', 0) > 20:
                score = 75.0
                category = 'warm'
            elif lead.get('budget') == 'low':
                score = 35.0
                category = 'cold'
                
            now_str = datetime.now().isoformat()
            
            # Insert
            try:
                c.execute("""
                    INSERT INTO leads (
                        user_id, name, email, company, phone, title,
                        source, campaign, medium, past_interactions, pages_visited, time_on_site,
                        company_size, industry, budget, notes, tags,
                        score, score_category, conversion_probability, status, converted, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    lead.get('name'),
                    lead.get('email'),
                    lead.get('company'),
                    lead.get('phone'),
                    lead.get('title'),
                    lead.get('source'),
                    lead.get('campaign'),
                    lead.get('medium'),
                    lead.get('past_interactions', 0),
                    lead.get('pages_visited', 0),
                    lead.get('time_on_site', 0),
                    lead.get('company_size'),
                    lead.get('industry'),
                    lead.get('budget'),
                    lead.get('notes'),
                    lead.get('tags'),
                    score,
                    category,
                    score/100.0,
                    status,
                    0, # converted (False)
                    now_str
                ))
                user_count += 1
                total_added += 1
            except Exception as e:
                print(f"Failed to insert lead {lead.get('email')}: {e}")
        print(f"    Added {user_count} leads.")
    
    conn.commit()
    conn.close()
    print(f"Success! Added {total_added} new leads across {len(users)} users.")

if __name__ == '__main__':
    seed()
