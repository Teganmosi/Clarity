from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
from ..database import get_db
from ..models import Lead
from ..auth import get_current_user
from ..services.intent_engine import calculate_intent_score

router = APIRouter(prefix="/intent", tags=["Intent"])


@router.post("/analyze/{lead_id}")
async def analyze_lead_intent(
    lead_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    result = calculate_intent_score(lead)
    lead.intent_score = result["intent_score"]
    lead.intent_signals = result["intent_signals"]
    lead.last_intent_check = result["last_intent_check"]
    db.commit()
    return {
        "lead_id": lead_id,
        "intent_score": result["intent_score"],
        "intent_signals": result["intent_signals"],
        "last_intent_check": result["last_intent_check"].isoformat(),
    }


@router.get("/high-priority")
async def get_high_priority_leads(
    threshold: int = 75,
    db: Session = Depends(get_db)
):
    leads = db.query(Lead).filter(Lead.intent_score >= threshold).all()
    return {
        "total": len(leads),
        "threshold": threshold,
        "leads": [
            {
                "id": l.id,
                "name": l.name,
                "company": l.company,
                "intent_score": l.intent_score,
                "intent_signals": l.intent_signals or [],
                "last_intent_check": l.last_intent_check.isoformat() if l.last_intent_check else None,
            }
            for l in leads
        ],
    }


@router.post("/analyze-all")
async def analyze_all_leads(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    leads = db.query(Lead).all()
    count = 0
    for lead in leads:
        result = calculate_intent_score(lead)
        lead.intent_score = result["intent_score"]
        lead.intent_signals = result["intent_signals"]
        lead.last_intent_check = result["last_intent_check"]
        count += 1
    db.commit()
    return {
        "message": f"Intent analysis completed for {count} leads",
        "total_analyzed": count,
    }
