import json
import sys
import os
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import Base, User, Lead
from app.scoring import score_leads
from datetime import datetime

# Initialize DB connection
db = SessionLocal()

def seed_data():
    try:
        # Get first user
        user = db.query(User).first()
        if not user:
            print("Error: No user found in database. Please register a user via the UI first.")
            return

        print(f"Seeding data for user: {user.username} ({user.email})")

        # Load sample data
        json_path = os.path.join(os.path.dirname(__file__), '..', 'sample-leads.json')
        if not os.path.exists(json_path):
             # Try current directory if running from root
             json_path = 'sample-leads.json'
        
        with open(json_path, 'r') as f:
            leads_data = json.load(f)

        print(f"Loaded {len(leads_data)} leads from {json_path}")

        # Score leads
        print("Scoring leads...")
        scored_leads = score_leads(leads_data)

        # Insert into DB
        print("Inserting into database...")
        count = 0
        for i, lead_data in enumerate(leads_data): # leads_data has raw data, scored_leads has scores
            # scored_leads[i] contains the scores
            scored = scored_leads[i]
            
            # Check if lead already exists (by email) -> strict check to avoid duplicates on re-run
            existing = db.query(Lead).filter(Lead.email == lead_data['email'], Lead.user_id == user.id).first()
            if existing:
                print(f"Skipping existing lead: {lead_data['email']}")
                continue

            db_lead = Lead(
                user_id=user.id,
                name=lead_data['name'],
                email=lead_data['email'],
                company=lead_data.get('company'),
                phone=lead_data.get('phone'),
                title=lead_data.get('title'),
                source=lead_data.get('source'),
                campaign=lead_data.get('campaign'),
                medium=lead_data.get('medium'),
                past_interactions=lead_data.get('past_interactions', 0),
                pages_visited=lead_data.get('pages_visited', 0),
                time_on_site=lead_data.get('time_on_site', 0),
                company_size=lead_data.get('company_size'),
                industry=lead_data.get('industry'),
                budget=lead_data.get('budget'),
                notes=lead_data.get('notes'),
                tags=lead_data.get('tags'),
                score=scored['score'],
                score_category=scored['score_category'],
                conversion_probability=scored['conversion_probability'],
                created_at=datetime.now(),
                status='new' # Default status
            )
            db.add(db_lead)
            count += 1
        
        db.commit()
        print(f"Successfully added {count} new leads.")

    except Exception as e:
        print(f"Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
